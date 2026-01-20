<# 
bootstrap.ps1
- pip 업그레이드
- ansible-core/ansible-lint/molecule 설치
- ansible-galaxy collection requirements.yml 설치
#>

$ErrorActionPreference = "Stop"

function Write-Err($msg) {
  Write-Host "[ERROR] $msg" -ForegroundColor Red
}

# python 확인
$pyCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
  $pyCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  # Windows Python Launcher
  $pyCmd = "py -3"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
  $pyCmd = "python3"
} else {
  Write-Err "python not found (install Python 3 and ensure it's on PATH)"
  exit 1
}

# pip 업그레이드 (조용히)
try {
  & $pyCmd -m pip install --upgrade pip | Out-Null
} catch {
  Write-Err "pip upgrade failed: $($_.Exception.Message)"
  exit 1
}

# 패키지 설치 (조용히)
try {
  & $pyCmd -m pip install "ansible-core>=2.15" ansible-lint molecule "molecule-plugins[docker]" | Out-Null
} catch {
  Write-Err "pip install failed: $($_.Exception.Message)"
  exit 1
}

# ansible-galaxy 실행 가능한지 확인 (pip로 설치되면 Scripts 경로에 생김)
if (-not (Get-Command ansible-galaxy -ErrorAction SilentlyContinue)) {
  Write-Err "ansible-galaxy not found on PATH. Reopen terminal or ensure Python Scripts path is added."
  # 참고로 진행을 멈추는 게 안전함
  exit 1
}

# requirements.yml 존재 확인
if (-not (Test-Path -Path "requirements.yml" -PathType Leaf)) {
  Write-Err "requirements.yml not found in current directory: $(Get-Location)"
  exit 1
}

# 컬렉션 설치
try {
  ansible-galaxy collection install -r requirements.yml
} catch {
  Write-Err "ansible-galaxy collection install failed: $($_.Exception.Message)"
  exit 1
}

Write-Host "OK: bootstrap complete"
