# Ansible

## VSCode + WSL 설정 (캡처 순서)

1) **VSCode에서 WSL 확장 확인**

![VSCode WSL 확장](image.png)

2) **WSL 연결 또는 Linux 설치**

![WSL 연결](image-1.png)

3) **WSL 배포판 연결/해제 확인**

![WSL 배포판](image-2.png)

4) **Windows 프로젝트 폴더를 WSL로 복제 후 VSCode 열기**

![폴더 열기](image-3.png)

5) **WSL 환경에서 Git 사용자 정보 재설정**

![Git 설정](image-4.png)

```bash
git config --global user.name "당신의 이름 또는 닉네임"
git config --global user.email "github에 등록된 이메일@example.com"
```
---
# Ansible 프로젝트에서 `Zone.Identifier` 파일 생성 방지 & 기존 파일 삭제 가이드

`Zone.Identifier`는 Windows의 **Mark-of-the-Web(MOTW)** / **Attachment Manager**가 파일에 “인터넷에서 내려받은 파일” 같은 **영역(Zone) 정보**를 기록하면서 생기는 메타정보입니다.  
Windows + WSL/공유폴더/NTFS 마운트 같은 환경에서는 이 정보가 리눅스 쪽에서 `*.Zone.Identifier` 또는 `*:Zone.Identifier` 같은 **파일 형태로 보이거나 생성**될 수 있습니다.

아래는 **(1) 앞으로 생성되지 않게 막는 방법**과 **(2) 이미 생성된 파일을 삭제하는 방법**을 정리한 문서입니다.

---

## 1) 앞으로 생성되지 않게 막기 (원인별)

### A. Windows(호스트)가 생성하는 경우 (가장 흔함: WSL/공유폴더/Windows에서 복사/다운로드)
Windows에서 Attachment Manager가 Zone 정보를 저장하지 않도록 설정하면, 이후 새로 내려받는/복사하는 파일에 **Zone.Identifier가 더 이상 붙지 않도록** 할 수 있습니다.

#### 1) 그룹 정책(gpedit.msc)
- 경로:
  - `사용자 구성 → 관리 템플릿 → Windows 구성 요소 → 첨부 파일 관리자`
- 설정:
  - **“파일 첨부에서 영역 정보 보존 안 함”** → **사용(Enabled)**

#### 2) 레지스트리(그룹 정책이 없는 에디션 포함)
- 키:
  - `HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Attachments`
- 값:
  - `DWORD (32-bit) SaveZoneInformation = 1`  (영역 정보 저장 안 함)

> 위 설정 후에는 Windows에서 새로 생성/다운로드/복사된 파일에 Zone 정보가 덜 붙습니다.

---

### B. 프로젝트가 NTFS로 마운트된 경로에 있을 때 (리눅스에서 NTFS 파티션/외장하드 작업)
NTFS-3G 마운트 옵션에 따라 ADS(Alternate Data Streams)가 `:Zone.Identifier` 같은 형태로 **파일처럼 노출**될 수 있습니다.

#### 1) 현재 마운트 옵션 확인
```bash
mount | grep -E 'ntfs|ntfs-3g'
```

#### 2) `/etc/fstab`에서 `streams_interface` 조정(예시)
- ADS를 아예 안 보이게/막고 싶으면 `none`
- ADS를 xattr로 매핑하려면 `xattr`

```fstab
UUID=XXXX  /mnt/data  ntfs-3g  defaults,streams_interface=none  0  0
# 또는
UUID=XXXX  /mnt/data  ntfs-3g  defaults,streams_interface=xattr 0  0
```

> 기존에 `streams_interface=windows` 형태라면 `file:Zone.Identifier`가 더 쉽게 드러날 수 있습니다.

---

## 2) 기존에 생성된 Zone.Identifier 파일 삭제 (리눅스)

아래는 **Ansible 프로젝트 루트**에서 실행한다고 가정합니다.

### (1) 삭제 대상 미리보기(추천)
```bash
cd /path/to/ansible-project

find . -type f \(   -name '*Zone.Identifier' -o   -name '*:Zone.Identifier*' -o   -name '*Zone.Identifier:$DATA*' -o   -name '*.Zone.Identifier*' \) -print
```

### (2) 실제 삭제
```bash
find . -type f \(   -name '*Zone.Identifier' -o   -name '*:Zone.Identifier*' -o   -name '*Zone.Identifier:$DATA*' -o   -name '*.Zone.Identifier*' \) -print -delete
```

> `*:Zone.Identifier*` 패턴은 NTFS ADS가 “콜론 파일명”으로 보이는 케이스까지 같이 정리하기 위한 옵션입니다.

---

## 3) Git에 실수로 올라가지 않게 방지 (.gitignore)
근본 차단은 아니지만, 리포지토리에 섞여 커밋되는 건 막아두는 게 좋습니다.

`.gitignore`에 추가:
```gitignore
*Zone.Identifier*
*:Zone.Identifier*
```

---

## 요약
- **생성을 근본적으로 막기(가장 흔한 케이스)**: Windows Attachment Manager 설정(그룹정책/레지스트리)
- **NTFS 마운트에서 파일처럼 보이는 문제**: `streams_interface=none` 또는 `xattr` 검토
- **이미 생긴 파일 정리**: `find ... -delete`로 프로젝트 내 일괄 삭제
- **커밋 방지**: `.gitignore` 패턴 추가

---

## 환경 준비

- Linux/WSL(권장), 또는 macOS
- Python 3.9+
- Ansible (ansible-core)
- AWS 자격증명(Access Key / Secret Key 또는 SSO/프로파일)

## 설치

```bash
./scripts/bootstrap.sh
./scripts/check.sh
```

### 권한 문제 발생 시

```bash
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
```

### PEP 668 정책(Externally Managed Environment) 대응

Ubuntu/Debian이 시스템 Python에 pip 전역 설치를 막는 환경(23.10+/24.04, Python 3.12 등)에서는 venv 사용을 권장합니다.

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-full

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip setuptools wheel
python -m pip install "ansible>=9" ansible-lint molecule "molecule-plugins[docker]" docker
ansible-galaxy collection install -r requirements.yml
```

### 설치 확인

```bash
ansible --version
ansible-galaxy collection list | head -n 5
```

---

## 로컬에서 플레이북 실행 확인

```bash
source .venv/bin/activate
ansible -i inventories/dev/hosts.ini all -m ping
```

```bash
ansible-playbook -i inventories/dev/hosts.ini playbooks/00_ping.yml
```

### 콜백 플러그인 오류 해결 (ansible-core 2.13+)

```bash
sed -i 's/^stdout_callback *= *community\.general\.yaml/stdout_callback = ansible.builtin.default/' ansible.cfg
grep -q '^result_format' ansible.cfg || printf '\nresult_format = yaml\n' >> ansible.cfg
```

---

## Ansible 학습용 단계별 플레이북

아래 학습용 플레이북들은 **로컬 환경**에서 실행 가능한 예제입니다.

| 단계 | 파일 | 학습 포인트 | 실행 예시 |
| --- | --- | --- | --- |
| 01 | `playbooks/learning/01_ping.yml` | 가장 기본적인 Ping 모듈 | `ansible-playbook -i inventories/local/hosts.ini playbooks/learning/01_ping.yml` |
| 02 | `playbooks/learning/02_vars.yml` | 변수/팩트/`set_fact` | `ansible-playbook -i inventories/local/hosts.ini playbooks/learning/02_vars.yml` |
| 03 | `playbooks/learning/03_loop_when.yml` | loop + when 조건 | `ansible-playbook -i inventories/local/hosts.ini playbooks/learning/03_loop_when.yml` |
| 04 | `playbooks/learning/04_template_handler.yml` | template + handler | `ansible-playbook -i inventories/local/hosts.ini playbooks/learning/04_template_handler.yml` |

> 결과 파일은 `/tmp/ansible-learning`에 생성됩니다.

---

## 기본 테스트

```bash
ansible -i inventories/local/hosts.ini local -m ping
ansible-playbook playbooks/00_ping.yml
```

## 참고 사항

1. `docs/01_basics.md` : Ansible가 무엇이고, ad-hoc 명령/모듈 실행
2. `docs/02_inventory_vars.md` : 인벤토리/변수/팩트/조건문
3. `docs/03_playbooks_roles.md` : 플레이북 구조, Role로 분리
4. `docs/04_templates_handlers.md` : Jinja2 템플릿, 핸들러, idempotent 개념
5. `docs/05_vault_secrets.md` : Vault로 시크릿 관리

### 등등 docs 폴더 참조

---

## Nginx 설치 (로컬)

```bash
ansible-playbook -i inventories/local/hosts.ini playbooks/02_nginx.yml
```

권한 문제가 있으면 아래처럼 실행하세요.

```bash
ansible-playbook -i inventories/local/hosts.ini playbooks/02_nginx.yml --become --ask-become-pass
```

### Role 기반 웹서버 배포

```bash
ansible-playbook -i inventories/local/hosts.ini playbooks/03_role_web.yml
```

### Docker 호스트에 엔진 설치

```bash
ansible-playbook -i inventories/docker/hosts.ini playbooks/10_docker_install.yml
```

### AWS VPC + EC2 만들기

```bash
# AWS 자격 증명은 환경변수 또는 ~/.aws/credentials(프로파일)로 설정
ansible-playbook playbooks/20_aws_create_vpc.yml -e aws_region=ap-northeast-2
ansible-playbook playbooks/21_aws_create_ec2.yml -e aws_region=ap-northeast-2
```

> 비용이 발생할 수 있으니, 실습 후 `playbooks/23_aws_cleanup.yml`로 정리하세요.

## Docker 엔진 설치 → Compose 배포

```bash
ansible-playbook -i inventories/dev/hosts.ini playbooks/10_docker_engine_install.yml
```

비밀번호 입력 문제가 있으면 아래처럼 실행합니다.

```bash
ansible-playbook -i inventories/dev/hosts.ini playbooks/10_docker_engine_install.yml -K
```

```bash
ansible-playbook -i inventories/dev/hosts.ini playbooks/11_deploy_stack.yml
```

## Rolling 배포(멀티 호스트)

```bash
ansible-playbook -i inventories/prod/hosts.ini playbooks/12_deploy_stack_rolling.yml
```

## Blue-Green 배포(단일 호스트)

```bash
ansible-playbook -i inventories/dev/hosts.ini playbooks/13_blue_green_switch.yml
```

## AWS (SSM 기반, SSH 없이)

- 문서: `docs/06_ssm_connection.md`

원샷 프로비저닝(EC2 생성 + SSM 역할/프로파일 + 태그):

```bash
ansible-playbook playbooks/20_aws_provision_ssm_no_ssh.yml \
  -e aws_region=ap-northeast-2 \
  -e environment=dev

ansible-inventory -i inventories/aws/aws_ec2.yml --graph
```

SSM로 구성/배포(SSH 없이):

```bash
ansible-playbook -i inventories/aws/aws_ec2.yml playbooks/21_post_provision_via_ssm.yml
```

정리(비용 방지):

```bash
ansible-playbook playbooks/23_aws_cleanup.yml -e aws_region=ap-northeast-2 -e environment=dev
```
---
## 자세한 단계별 가이드는 `docs/`를 참고하세요.
---

### 구성:
- **Trivy**: 컨테이너/이미지 취약점 스캐너 (리포트 생성)
- **Docker Bench for Security**: 도커 호스트 보안 점검(베스트프랙티스 체크리스트)
- **CrowdSec + Nginx(옵션)**: Nginx 로그를 기반으로 탐지/알림을 확인하는 실습

> 실습 목적: “도커 기반 보안 도구를 Ansible로 배포/실행/결과물 생성”까지 한 번에 경험.

---

## 0) 사전 준비

- Linux(Ubuntu/Debian 권장)
- Ansible 설치
- (권장) sudo 권한

### Ansible collection 설치
본 랩은 `community.docker` collection을 사용합니다.

```bash
ansible-galaxy collection install -r requirements.yml
```

---

## 1) Docker 설치 (필요한 경우만)

Docker가 아직 없다면 아래 playbook을 실행하세요.

```bash
ansible-playbook playbooks/00_bootstrap.yml -K
```

- `-K`는 sudo 비밀번호 입력을 위해 필요할 수 있습니다.
- 실행 후, 현재 사용자를 docker 그룹에 추가하므로 **재로그인**이 필요할 수 있습니다.

---

## Trivy(트리비)로 이미지 취약점 스캔

기본 스캔 대상은 `nginx:latest` 입니다 (`group_vars/all.yml`에서 변경 가능).

```bash
ansible-playbook -i inventories/local/hosts.ini playbooks/91_trivy_scan.yml -K
```

결과물:
- `/opt/security-lab/reports/` 아래에 리포트 저장
  - `trivy-nginx_latest.json`
  - `trivy-nginx_latest.txt`

리포트를 빠르게 확인하려면:
```bash
ls -al /opt/security-lab/reports
sed -n '1,120p' /opt/security-lab/reports/trivy-nginx_latest.txt
```
```
sudo apt install xdg-utils
xdg-open /opt/security-lab/reports/trivy-nginx_latest.html
cd /opt/security-lab/reports
python3 -m http.server 8000 --bind 0.0.0.0
```
---

## 3) Docker Bench for Security로 호스트 점검

```bash
ansible-playbook playbooks/02_docker_bench.yml -K
```

결과물:
- `/opt/security-lab/reports/docker-bench-YYYYMMDD-HHMMSS.txt`

---

## 4) (옵션) CrowdSec + Nginx 로그 기반 탐지 실습

`group_vars/all.yml`의 `enable_crowdsec_lab: true`일 때 동작합니다.

```bash
ansible-playbook playbooks/03_crowdsec_nginx_lab.yml -K
```

### 4-1) 로그 생성(트래픽 발생)
```bash
curl -sS http://localhost:8080/
curl -i  http://localhost:8080/notfound
```

조금 더 많이 찍고 싶으면:
```bash
for i in {1..50}; do curl -sS http://localhost:8080/notfound >/dev/null; done
```

### 4-2) CrowdSec 상태/지표 확인
```bash
docker exec -it lab-crowdsec cscli metrics
docker exec -it lab-crowdsec cscli alerts list
```

> CrowdSec는 시나리오/컬렉션/파서 구성에 따라 탐지 결과가 달라집니다.  
> 이 랩은 “로그를 읽고 상태/알림을 확인하는 흐름”을 익히는 데 초점을 둡니다.

---

## 커스터마이징 포인트

### 스캔 대상 이미지 바꾸기
`group_vars/all.yml`에서:
```yaml
scan_image: "alpine:3.21"
```
처럼 변경한 뒤 Trivy playbook을 재실행하세요.

### 설치 경로 바꾸기
`lab_root` 값을 바꾸면 `/opt/security-lab` 대신 다른 경로를 사용할 수 있습니다.

---


---

## 빠른 실행 요약

```bash
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/00_bootstrap.yml -K
ansible-playbook playbooks/01_trivy_scan.yml -K
ansible-playbook playbooks/02_docker_bench.yml -K
ansible-playbook playbooks/03_crowdsec_nginx_lab.yml -K
```
