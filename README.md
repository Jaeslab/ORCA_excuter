# DFT_auto (EASY ORCA INP GENERATOR)

ORCA `.inp` 파일을 대화식으로 생성해주는 스크립트입니다. `ver2-1.py`를 실행하면 몇 가지 질문에 답하는 것만으로 `분자이름_계산종류.inp` 파일이 만들어지고, 원하면 바로 이어서 ORCA 실행 + 진행 상황 확인 + 결과 요약까지 해줍니다.

> 폴더에 `main.py`, `ver20.py`, `ver2-1.py`가 같이 있는데, 현재 활발히 수정 중인 최신 버전은 **`ver2-1.py`**입니다. 이 문서도 `ver2-1.py` 기준으로 작성되었습니다.

질문들은 화면에 계속 쌓이지 않고, 답할 때마다 같은 자리에서 다음 질문으로 갱신됩니다.

## 설치 (Windows / macOS 공통)

`ver2-1.py`는 `glob`, `os`, `re`, `shutil`, `subprocess`, `sys`, `time`처럼 파이썬 표준 라이브러리만 씁니다. 별도 `pip install`은 필요 없고, 아래 두 가지만 있으면 됩니다.

- **Python 3** (3.8 이상 권장) — f-string 등을 쓰므로 3.6 미만은 안 됩니다.
- **ORCA 프로그램 본체** — ORCA 자체를 실행/설치하는 것과는 별개로, 이 스크립트는 `.inp` 파일만 만들어주는 도구입니다. ORCA로 바로 계산까지 돌리고 싶으면 [ORCA Forum](https://orcaforum.kofo.mpg.de)에서 가입 후 무료로 받을 수 있습니다.
- **(선택) MPI** — 코어 2개 이상으로 병렬 계산(`%pal nprocs`)을 돌릴 경우, ORCA 다운로드 페이지에 적힌 것과 **정확히 같은 버전**의 MPI(Windows는 MS-MPI, macOS/Linux는 OpenMPI)가 필요합니다. 버전이 다르면 병렬 계산이 아예 안 돌거나 알 수 없는 에러로 죽는 경우가 많으니, Homebrew 등으로 아무 버전이나 설치하지 말고 ORCA 매뉴얼에 명시된 버전을 그대로 쓰세요.

### Windows에서

1. [python.org](https://www.python.org/downloads/windows/)에서 설치 파일을 받아 실행합니다. **설치 첫 화면에서 "Add python.exe to PATH" 체크박스를 반드시 켜세요** — 안 켜면 명령 프롬프트에서 `python`을 못 찾습니다.
2. ORCA는 받은 압축 파일을 원하는 폴더에 그냥 풀면 됩니다 (예: `C:\orca_6_0_1`). 설치 프로그램은 따로 없습니다.
3. 병렬 계산을 쓸 거면 ORCA가 요구하는 버전의 MS-MPI(`msmpisetup.exe`, `msmpisdk.msi`)를 설치합니다.
4. `ver2-1.py`와 계산할 `.xyz`/`.inp` 파일들을 같은 폴더에 넣고, PowerShell(또는 명령 프롬프트)에서:
   ```powershell
   cd C:\원하는\작업폴더
   python ver2-1.py
   ```
5. ORCA 실행파일 경로를 물어보면 `C:\orca_6_0_1\orca.exe`처럼 `.exe`까지 포함한 전체 경로를 입력합니다.
6. ⚠️ 구버전 `cmd.exe`(옛날 명령 프롬프트)는 이 스크립트가 화면을 지우는 데 쓰는 ANSI 이스케이프 코드를 제대로 처리 못해서 질문이 안 지워지고 이상한 문자가 보일 수 있습니다. Windows 10/11 기본 Windows Terminal이나 PowerShell에서는 정상적으로 동작합니다.

### macOS에서

1. `python3 --version`으로 먼저 확인해보세요. macOS 버전에 따라 Python 3가 없거나 오래된 경우가 있어서, 없으면 [python.org](https://www.python.org/downloads/macos/)에서 받거나 Homebrew로 설치합니다.
   ```bash
   brew install python
   ```
2. ORCA는 받은 압축 파일(.tar.xz 등)을 원하는 위치에 풀면 됩니다 (예: `/opt/orca_6_0_1`). Apple Silicon(M1/M2/M3 등)이면 arm64용 빌드를, Intel Mac이면 x86_64용 빌드를 받아야 합니다.
3. 병렬 계산을 쓸 거면 ORCA가 요구하는 버전의 OpenMPI를 설치합니다. `brew install open-mpi`는 최신 버전이 깔려서 ORCA가 요구하는 버전과 다를 수 있으니, 가능하면 ORCA 매뉴얼/다운로드 페이지에 적힌 버전으로 맞추세요.
4. 터미널(Terminal.app, iTerm2 등)에서:
   ```bash
   cd ~/원하는/작업폴더
   python3 ver2-1.py
   ```
5. ORCA 실행파일 경로를 물어보면 `/opt/orca_6_0_1/orca`처럼 확장자 없는 전체 경로를 입력합니다.

## 준비물

- 계산할 분자의 구조 정보(`.xyz` 파일, 또는 구조가 들어있는 `.inp` 파일)를 `ver2-1.py`와 같은 디렉토리에 둡니다.
- ESD 계산을 할 경우, 미리 계산해둔 Hessian(`.hess`) 파일이 필요합니다 (아래 ESD 항목 참고). 이 파일은 4번(DFT single Freq)/5번(TDDFT Numfreq) 계산으로 직접 만들 수 있습니다.
- ORCA로 바로 실행까지 하고 싶다면 ORCA 실행파일이 있어야 합니다.

## 실행

macOS/Linux:
```bash
python3 ver2-1.py
```

Windows:
```powershell
python ver2-1.py
```

## 1. 분자 구조 선택

```
xyz파일이 별도로 존재합니까? [y/n]
```

- **y**: 현재 폴더의 `.xyz` 파일 목록에서 하나를 고릅니다. 선택한 파일명(확장자 제외)이 분자 이름이 되고, `.inp`는 `* xyzfile <charge> <mult> 파일명.xyz` 형태로 그 파일을 참조합니다. `.xyz` 파일이 하나도 없으면 메시지를 띄우고 다시 처음 질문("xyz파일이 별도로 존재합니까?")으로 돌아갑니다.
- **n**: 이어서 "별도의 inp파일의 분자구조를 이용하시겠습니까??"를 물어봅니다.
  - **y**: 현재 폴더의 `.inp` 파일 목록에서 하나를 고르면, 그 안에서 구조 정보를 읽어옵니다.
    - 고른 `.inp`가 `* xyzfile ...` 형식이면 그 참조 파일명만 그대로 가져다 씁니다.
    - `* xyz ...` ~ `*`로 된 좌표 블록이면 좌표를 통째로 복사해서 새 `.inp`에 그대로 넣습니다. 이때 전하/다중도는 원본 파일 값이 아니라 뒤의 3번 단계에서 새로 입력하는 값으로 덮어씁니다.
    - `.inp` 파일이 하나도 없으면 메시지를 띄우고 다시 처음 질문으로 돌아갑니다.
  - **n**: 분자 이름을 직접 입력받는 절차가 없어서, 다시 처음 질문("xyz파일이 별도로 존재합니까?")으로 돌아갑니다 — 결국 xyz든 inp든 구조를 하나 골라야 이 단계를 빠져나갈 수 있습니다.

## 2. 계산 종류 선택

```
원하는 계산을 선택해주세요
0. DFT single point
1. DFT opt
2. TDDFT single point
3. TDDFT opt
4. DFT single Freq
5. TDDFT Numfreq
6. ESD
7. SOCME
8. NACME
9. import inp
```

| 번호 | 계산 종류 | 추가되는 키워드 | 생성 파일명 접미사 |
|---|---|---|---|
| 0 | DFT 싱글포인트 | (없음) | `_dft_single` |
| 1 | DFT 지오메트리 최적화 | `Opt` | `_dft_opt` |
| 2 | TDDFT 싱글포인트 (여러 들뜬상태 에너지) | (없음) | `_tddft_single` |
| 3 | TDDFT 최적화 (특정 들뜬상태 구조 최적화) | `Opt` | `_tddft_opt` |
| 4 | DFT single Freq (바닥상태 Hessian 계산) | `Freq` | `_dft_freq` |
| 5 | TDDFT Numfreq (들뜬상태 Hessian 계산) | `NumFreq` | `_tddft_numfreq` |
| 6 | ESD (형광/흡수/인광 스펙트럼) | `ESD(...)` | `_esd` |
| 7 | SOCME (스핀-궤도 커플링) | `RI-SOMF(1X)` | `_socme` |
| 8 | NACME (비단열 커플링) | `NumGrad` | `_nacme` |
| 9 | import inp (기존 `.inp` 재사용) | - | - |

- 4번, 5번은 이미 최적화된 구조(1번/3번 결과)에 대해 진동수(Hessian)를 계산하는 용도입니다. 여기서 나온 `.hess` 파일이 ESD(6번)의 `GSHESSIAN`/`ESHESSIAN`/`TSHESSIAN` 입력값이 됩니다.
- 5번(TDDFT Numfreq)은 어떤 들뜬상태의 Hessian을 구할지 지정해야 하므로 TDDFT 설정(아래 4번 항목)이 같이 나옵니다.
- **7번 SOCME**: 스핀 다중도가 **다른** 상태 사이의 커플링(예: S1-T1) — 인터시스템 크로싱(ISC)/인광 속도 계산에 씀. `%tddft`에 `dosoc true`, `triplets true`가 항상 붙고, SOC는 full TDDFT가 필요해서 TDA는 사용자 선택과 무관하게 항상 꺼집니다(`tda false`). functional 앞에는 항상 `ZORA `가 붙습니다.
- **8번 NACME**: 스핀 다중도가 **같은** 상태 사이의 커플링(바닥상태와 `iroot`로 지정한 들뜬상태, 예: S0-S1) — 내부전환(internal conversion), 원뿔형 교차 근처 무복사 전이 경로를 볼 때 씀. `%tddft`에 `nacme true`, `etf true`가 붙습니다.
- **9번 import inp**: 새로 값을 입력받지 않고, 현재 폴더의 `.inp` 목록에서 고른 파일을 그대로 읽어 화면에 출력한 뒤 바로 9번(ORCA 실행 여부) 단계로 넘어갑니다.

## 3. Functional / Basis set / 전하·다중도 선택

```
choose functional
0.HF 1.B3lyp 2.CAM-B3lyp 3.wB97x-d4 4.PBE 5.WB97X-2

choose basis
0.STO-3g 1.3-21G 2.6-31G 3.6-31G(d)
4.6-31G(d,p) 5.def2-SVP 6.def2-TZVP 7.6-31++G(d,p)
```

메뉴에 안 보이는 분산 보정(D3BJ)이 일부 functional에는 자동으로 붙습니다.

| 번호 | 메뉴 표시 | 실제 `.inp` 키워드 |
|---|---|---|
| 0 | HF | `HF` |
| 1 | B3lyp | `B3LYP D3BJ` |
| 2 | CAM-B3lyp | `CAM-B3LYP D3BJ` |
| 3 | wB97x-d4 | `wB97X-D4` |
| 4 | PBE | `PBE D3BJ` |
| 5 | WB97X-2 | `WB97X-2` |

Basis는 번호 그대로(`STO-3G`, `3-21G`, `6-31G`, `6-31G(d)`, `6-31G(d,p)`, `def2-SVP`, `def2-TZVP`, `6-31++G(d,p)`) 들어갑니다. 단, **SOCME(7번)을 고르고 basis가 `def2-SVP`/`def2-TZVP`면 자동으로 `ZORA-def2-SVP`/`ZORA-def2-TZVP`로 바뀝니다** (다른 basis는 안 바뀌니 주의).

이어서 전하/다중도를 입력합니다.

```
분자의 전하(Charge)를 입력하세요 (기본: 0, 양이온: 1, 음이온: -1)
분자의 스핀 다중도(Multiplicity)를 입력하세요 (단일항: 1, 삼중항: 3, 래디컬: 2 / 기본: 1)
```

엔터만 치면 각각 기본값(전하 0, 다중도 1)이 적용됩니다. 여기서 입력한 값이 `* xyzfile <charge> <mult> ...` / `* xyz <charge> <mult>` 줄에 들어갑니다 — `.inp`에서 구조를 가져온 경우에도 원본에 있던 전하/다중도는 무시되고 여기서 새로 입력한 값으로 교체됩니다.

## 4. TDDFT 설정 (계산 종류가 TDDFT/Numfreq/ESD/SOCME/NACME일 때만 표시)

- **TDDFT 싱글포인트, TDDFT 최적화, TDDFT Numfreq, ESD, SOCME, NACME**(2, 3, 5, 6, 7, 8번) 선택 시: 고려할 들뜬상태 개수(`nroots`)를 입력합니다.
- **TDDFT 최적화, TDDFT Numfreq, ESD, NACME**(3, 5, 6, 8번) 선택 시: 대상이 될 들뜬상태 번호(`iroot`, 보통 1이면 S1/T1)를 추가로 입력합니다. SOCME(7번)은 특정 상태 하나를 지정하지 않고 커플링 가능한 상태 쌍을 전부 계산하므로 iroot를 묻지 않습니다.

## 5. ESD 설정 (계산 종류가 ESD일 때만 표시)

```
ESD 종류를 선택하세요
0. 형광(FLUOR)
1. 흡수(ABS)
2. 인광(PHOSP)
```

이후 이미 계산해둔 Hessian 파일명을 입력합니다.

- **형광(FLUOR) / 흡수(ABS)**: 바닥상태 Hessian(`GSHESSIAN`), 들뜬상태 Hessian(`ESHESSIAN`) 파일명
- **인광(PHOSP)**: 바닥상태 Hessian, 삼중항 Hessian(`TSHESSIAN`) 파일명, 그리고 바닥-삼중항 에너지차 `DELE`(cm⁻¹)
  - PHOSP는 스핀-궤도 커플링 계산이 필요해서 `RI-SOMF(1X)` 근사와 `%tddft`의 `DOSOC TRUE`/`TDA FALSE`가 자동으로 추가됩니다.

마지막으로 Herzberg-Teller 진동커플링(`DOHT`) 적용 여부, 그리고 Huang-Rhys factor 등 진동모드별 상세정보(`PRINTLEVEL 3`) 표시 여부를 y/n으로 묻습니다.

> Hessian 파일은 4번(DFT single Freq)/5번(TDDFT Numfreq) 계산으로 미리 만들어 둬야 합니다 — ESD 자체는 처음부터 전부 계산해주는 원샷 기능이 아닙니다.

## 6. 근사 방법 (RIJCOSX 등) 적용 여부

기본적으로는 아무것도 묻지 않고 `RIJCOSX AutoAux`가 자동으로 붙습니다. **DFT opt(1번)를 선택했을 때만** 다음 질문이 나옵니다.

```
RI-JK 적용 동의하십니까? [y/n]
```

- `y`: functional이 HF면 `RI-JK AutoAux`로, 그 외 functional이면 `AutoAux`만 붙습니다 (ORCA는 `AutoAux`만 있어도 적절한 RI 근사를 자동으로 적용합니다).
- `n`: 기본값인 `RIJCOSX AutoAux`가 그대로 유지됩니다.
- 1번 외의 계산 종류는 이 질문 자체가 안 나오므로 항상 `RIJCOSX AutoAux`입니다.

TDDFT 관련 계산(2, 3, 5, 6, 7, 8번)이면 이어서 TDA(Tamm-Dancoff) 근사 적용 여부도 물어봅니다. PHOSP(인광) ESD와 SOCME은 스핀-궤도 커플링 계산 특성상 이 선택과 무관하게 항상 `tda false`로 강제됩니다.

## 7. TIGHTSCF 적용 여부

계산 종류와 상관없이 매번 물어봅니다.

```
타이트 적용 동의하십니까? [y/n]
```

`y`면 `TIGHTSCF` 키워드가 붙습니다.

## 8. 계산 사양 (코어 수 / 메모리)

같은 폴더에 `spec.txt`가 있으면 저장된 코어 수/메모리를 보여주고 그대로 쓸지 물어봅니다.

```
저장된 계산 사양(코어 4, 코어당 메모리 1GB)을 씁니다. 수정하시겠습니까? [y/n]
```

`y`로 답해 새 값을 입력하면 `spec.txt`도 같이 갱신됩니다. `spec.txt`가 없으면 처음부터 새로 물어봅니다.

```
계산 사양 변경 원함??? [y/n]
```

`y`를 입력하면 코어 수와 코어당 메모리(GB)를 입력받아 `%pal nprocs`, `%maxcore` 블록이 추가되고 `spec.txt`에 저장됩니다. **코어 수를 1(기본값)로 두면 `%pal`/`%maxcore` 블록 자체가 생성되지 않습니다.**

## 9. `.inp` 저장 후 바로 ORCA 실행할지 여부

```
지금 바로 ORCA로 실행하시겠습니까? [y/n]
```

`y`를 입력하면:

1. **ORCA 실행파일 경로**를 찾습니다.
   - `orca_pos.txt` 파일이 같은 폴더에 있으면, 그 안에 적힌 경로를 그대로 쓰고 다시 묻지 않습니다.
     - 단, 그 경로에 실제 파일이 없으면 `잘못된 경로!!!`를 출력하고 프로그램이 즉시 종료됩니다.
   - `orca_pos.txt`가 없으면 경로를 직접 입력받습니다 (엔터만 치면 기본값 `orca`, PATH에서 찾음). 입력한 경로가 실제로 존재하는 파일이면 다음번엔 안 물어보도록 `orca_pos.txt`에 자동 저장합니다.
2. `orca 분자이름_접미사.inp > 분자이름_접미사.out`을 백그라운드로 실행하면서, `.out` 파일을 실시간으로 읽어 진행 상황을 한 줄로 계속 갱신해서 보여줍니다.
   - `[SCF] n번째 SCF 계산 수렴 완료`
   - `[OPT] n번째 geometry 최적화 사이클 진행 중 (사이클당 평균 X초, 참고용 추정치)`
   - `[TDDFT] TDDFT 계산 진행 중...`
   - `[완료] ORCA TERMINATED NORMALLY`
3. 계산이 끝나면 요약을 출력합니다: 정상/비정상 종료 여부, 총 소요시간, 최종 에너지, SCF 계산 횟수, geometry 최적화 사이클 수.

> ⚠️ Geometry 최적화 사이클 배너나 TDDFT 진행 표시 문구는 실제 ORCA `.out` 샘플로 검증 전이라(설치된 ORCA가 없어 확인 못 함) 버전에 따라 안 맞을 수 있습니다. `ORCA TERMINATED NORMALLY`, `TOTAL RUN TIME`, `FINAL SINGLE POINT ENERGY`, `SCF CONVERGED AFTER N CYCLES`는 확인된 문구라 신뢰도가 높습니다.
> ORCA는 자체적으로 MPI를 호출하므로 `orca_pos.txt`/입력 경로에 `mpirun` 없이 ORCA 실행파일 경로만 넣어야 합니다.

### ORCA 실행파일 경로 설정 방법

경로는 스크립트를 실행하는 폴더에 있는 `orca_pos.txt`에 저장되어 재사용됩니다.

- **처음 실행할 때** (`orca_pos.txt`가 아직 없을 때) 경로를 물어봅니다.
  - 그냥 엔터만 치면 `PATH` 환경변수에서 `orca`라는 이름의 실행파일을 자동으로 찾습니다 (`shutil.which("orca")`).
  - 경로를 직접 입력하면 그 경로를 그대로 사용합니다.
  - 이렇게 정해진 경로가 실제 존재하는 파일이면 `orca_pos.txt`에 자동 저장되어, 다음부터는 다시 안 물어봅니다.
- **이미 `orca_pos.txt`가 있으면** 그 안의 경로를 무조건 그대로 씁니다. 그 경로에 파일이 없으면 `잘못된 경로!!!`를 출력하고 프로그램이 즉시 종료됩니다.
- **경로를 바꾸고 싶으면** `orca_pos.txt` 파일을 직접 열어서 내용을 고치거나 파일을 삭제하세요 (스크립트 안에 별도의 "경로 재설정" 메뉴는 없습니다). 삭제하면 다음 실행 때 다시 물어봅니다.
- ⚠️ **`PATH`에 등록된 `orca`(심볼릭 링크 등)보다는 설치 폴더의 절대경로를 직접 입력하는 걸 권장합니다.** ORCA는 병렬 계산(코어 2개 이상, `%pal nprocs`)을 실행할 때 자기 실행파일의 실제 경로를 기준으로 `orca_scf`, `orca_gtoint` 같은 보조 실행파일을 같은 폴더에서 찾습니다. 심볼릭 링크나 래퍼 스크립트를 거치면 이 탐색이 꼬여서 병렬 계산이 실패할 수 있습니다. 예: `/opt/orca_6_0_1/orca`
- `orca_pos.txt`는 실행 폴더마다 따로 생기므로, 다른 폴더에서 처음 실행하면 다시 한번 경로를 물어봅니다.

## 결과

모든 질문에 답하면 `분자이름_접미사.inp` 파일이 저장되고, 생성된 내용이 콘솔에도 출력됩니다. 파일 맨 앞에는 항상 `# EASY ORCA INP GENERATOR version2.1` 배너 주석이 한 줄 붙습니다(아래 예시에서는 생략).

### 예시: DFT 싱글포인트 (charge 0, mult 1, TIGHTSCF 적용)

```
! B3LYP D3BJ STO-3G RIJCOSX AutoAux TIGHTSCF
* xyzfile 0 1 a.xyz
```

### 예시: DFT single Freq (ESD용 바닥상태 Hessian 생성)

```
! B3LYP D3BJ STO-3G RIJCOSX AutoAux TIGHTSCF Freq
* xyzfile 0 1 a.xyz
```

### 예시: TDDFT Numfreq (ESD용 들뜬상태 Hessian 생성)

```
! B3LYP D3BJ STO-3G RIJCOSX AutoAux TIGHTSCF NumFreq

%tddft
 nroots 6
 iroot 1
 tda true
end
* xyzfile 0 1 a.xyz
```

### 예시: SOCME (스핀-궤도 커플링, def2-SVP 선택 시 ZORA-def2-SVP로 자동 치환)

```
! ZORA B3LYP D3BJ ZORA-def2-SVP RIJCOSX AutoAux RI-SOMF(1X)

%tddft
 nroots 10
 dosoc true
 triplets true
 tda false
end
* xyzfile 0 1 a.xyz
```

### 예시: NACME (비단열 커플링, S0-S2)

```
! B3LYP D3BJ STO-3G RIJCOSX AutoAux NumGrad

%tddft
 nroots 10
 iroot 2
 nacme true
 etf true
 tda true
end
* xyzfile 0 1 a.xyz
```

### 예시: ESD 형광 스펙트럼

```
! B3LYP D3BJ STO-3G RIJCOSX AutoAux TIGHTSCF ESD(FLUOR)

%tddft
 nroots 6
 iroot 1
 tda true
end

%esd
 GSHESSIAN "gs.hess"
 ESHESSIAN "s1.hess"
 DOHT TRUE
 LINES VOIGT
 LINEW 75
 INLINEW 200
end
* xyzfile 0 1 a.xyz
```

### 예시: 구조를 `.inp`에서 그대로 가져온 경우 (`* xyz` 좌표 블록)

```
! B3LYP D3BJ STO-3G RIJCOSX AutoAux
* xyz 0 1
 C   0.000000   0.000000   0.000000
 H   0.000000   0.000000   1.089000
*
```
