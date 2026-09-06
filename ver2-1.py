import glob
import os
import re
import shutil
import subprocess
import sys
import time
version = "2.1"
class gen_inp:
    def __init__(self):
        self.calc = 0 # 0이면 싱글포인트, 1이면 그라운드opt+freq 2면 tddft 3면 tddftopt...
        self.functional = 0
        self.basis = 0
        self.rj = 0
        self.tightscf = 0
        self.cores = 1
        self.mem = 1
        self.nroots = 0
        self.iroot = 1
        self.tda = 1 
        self.triplets = 0 
        self.iroot_mult = 0 
        self.esd_type = 0 
        self.gshess = ""
        self.eshess = ""
        self.tshess = ""
        self.dele = 0
        self.doht = 0
        self.printlevel = 0 
        self.total_text = ""
        self.file_text = ""
        self.molname = ""
        
        self.charge = 0
        self.mult = 1
        
        # [수정] .inp 파일에서 추출한 좌표 데이터를 저장할 변수 추가
        self.coords_lines = []
        self.xyz_file_ref = ""

    def calc_text_gen(self):
        temp = ""
        if self.calc == 1: 
            temp += " Opt"
        elif self.calc == 3: # TDDFT opt
            temp += " Opt"
        elif self.calc == 4: # DFT single Freq
            temp += " Freq"
        elif self.calc == 5: # TDDFT Numfreq
            temp += " NumFreq"
        elif self.calc == 6: # ESD
            temp += " "
            if self.esd_type == 0:
                temp += "ESD(FLUOR)"
            elif self.esd_type == 1:
                temp += "ESD(ABS)"
            elif self.esd_type == 2:
                temp += "ESD(PHOSP) RI-SOMF(1X)" 
        elif self.calc == 7: # SOCME
            temp += " RI-SOMF(1X)" 
        elif self.calc == 8: # NACME
            temp += " NumGrad"
        return temp

    def common_text_gen(self):
        temp = ""
        #=======functional========
        func = ""
        if self.functional == 0:
            func = "HF"
        elif self.functional == 1:
            func = "B3LYP D3BJ" 
        elif self.functional == 2:
            func = "CAM-B3LYP D3BJ" 
        elif self.functional == 3:
            func = "wB97X-D4" 
        elif self.functional == 4:
            func = "PBE D3BJ" 
        elif self.functional == 5:
            func = "WB97X-2" 

        if self.calc == 7:
            temp += "ZORA " + func
        else:
            temp += func

        #========basis===========
        temp += " "
        bas = ""
        if self.basis == 0: bas = "STO-3G"
        elif self.basis == 1: bas = "3-21G"
        elif self.basis == 2: bas = "6-31G"
        elif self.basis == 3: bas = "6-31G(d)"
        elif self.basis == 4: bas = "6-31G(d,p)"
        elif self.basis == 5: bas = "def2-SVP" 
        elif self.basis == 6: bas = "def2-TZVP" 
        elif self.basis == 7: bas = "6-31++G(d,p)"

        if self.calc == 7 and "def2" in bas:
            bas = bas.replace("def2", "ZORA-def2")
        temp += bas

        #=========rj=========
        if self.rj == 0: 
            temp += " RIJCOSX AutoAux"
        else:
            temp += " "
            if self.rj == 1 and self.functional == 0 and self.calc not in (2, 3, 5, 6, 7, 8): 
                temp += "RI-JK AutoAux"
            elif self.rj == 1:
                temp += "AutoAux"
                
        #========tightscf========
        # [수정] TDDFT 등에서 TIGHTSCF를 강제로 넣던 로직 제거 (원래대로 복구)
        if self.tightscf == 1:
            temp += " TIGHTSCF"
            
        return temp

    def spec_text_gen(self):
        temp = ""
        if self.cores == 1:
            return ""
        else:
            if self.mem == 0:
                temp = "\n\n%pal nprocs " + str(self.cores) + "\nend"
            elif self.mem != 0:
                temp = "\n\n%pal nprocs " + str(self.cores) + "\nend\n\n%maxcore " + str(self.mem)
        return temp

    def tddft_text_gen(self):
        temp = ""
        if self.calc in (2, 3, 5, 6, 7, 8):
            temp = "\n\n%tddft\n nroots " + str(self.nroots)
            if self.calc in (3, 5, 6, 8):
                temp += "\n iroot " + str(self.iroot)
            tda = self.tda
            if (self.calc == 6 and self.esd_type == 2) or self.calc == 7: 
                tda = 0
                temp += "\n dosoc true"
            if self.triplets == 1 or self.calc == 7: 
                temp += "\n triplets true"
            if self.iroot_mult == 1: 
                temp += "\n irootmult triplet"
            if self.calc == 7 and self.printlevel > 0:
                temp += "\n printlevel " + str(self.printlevel)
            if self.calc == 8: 
                temp += "\n nacme true\n etf true"
            temp += "\n tda " + ("true" if tda == 1 else "false")
            temp += "\nend"
            
        if self.calc == 3:
            temp += "\n\n%geom\n MaxIter 100\nend"
            
        return temp

    def esd_text_gen(self):
        temp = ""
        if self.calc == 6: 
            temp = "\n\n%esd\n GSHESSIAN \"" + self.gshess + "\""
            if self.esd_type == 2: 
                temp += "\n TSHESSIAN \"" + self.tshess + "\""
                temp += "\n DELE " + str(self.dele)
            else: 
                temp += "\n ESHESSIAN \"" + self.eshess + "\""
            if self.doht == 1:
                temp += "\n DOHT TRUE"
            if self.printlevel > 0: 
                temp += "\n PRINTLEVEL " + str(self.printlevel)
            temp += "\n LINES VOIGT\n LINEW 75\n INLINEW 200\nend"
        return temp

    def xyz_text_gen(self):
        # temp = ""
        # temp = "\n* xyzfile 0 1 " + self.molname + ".xyz\n\n"
        # return temp
        # [수정] 추출된 좌표가 있으면 그대로 쓰고, 새로 입력받은 전하/다중도 반영
        if self.coords_lines:
            temp = f"\n* xyz {self.charge} {self.mult}\n"
            for line in self.coords_lines:
                temp += line
            temp += "*\n\n"
            return temp
        elif self.xyz_file_ref:
            return f"\n* xyzfile {self.charge} {self.mult} {self.xyz_file_ref}\n\n"
        else:
            return f"\n* xyzfile {self.charge} {self.mult} {self.molname}.xyz\n\n"

    def gen_text(self):
        aftername = ""
        if self.calc == 0:
            aftername = "_dft_single"
        elif self.calc == 1:
            aftername = "_dft_opt"
        elif self.calc == 2:
            aftername = "_tddft_single"
        elif self.calc == 3:
            aftername = "_tddft_opt"
        elif self.calc == 4:
            aftername = "_dft_freq"
        elif self.calc == 5:
            aftername = "_tddft_numfreq"
        elif self.calc == 6:
            aftername = "_esd"
        elif self.calc == 7:
            aftername = "_socme"
        elif self.calc == 8:
            aftername = "_nacme"
            
        self.file_text = self.molname + aftername + ".inp"
        inst_text = "EASY ORCA INP GENERATOR version"+version + "\n"
        cond_text = self.common_text_gen()
        calc_text = self.calc_text_gen()
        tddft_text = self.tddft_text_gen()
        esd_text = self.esd_text_gen()
        spec_text = self.spec_text_gen()
        xyz_text = self.xyz_text_gen()
        
        self.total_text = "# " + inst_text + "! " + cond_text + calc_text + tddft_text + esd_text + spec_text + xyz_text

    def text_save(self):
        with open(self.file_text, 'w', encoding = "utf-8") as f:
            f.write(self.total_text)
            print(self.total_text)
        return 0

    def text_load(self):
        with open(self.file_text, 'r', encoding="utf-8") as f:
            self.total_text = f.read()
        print(self.total_text)
        return 0

class chooser:
    def __init__(self):
        self.geninp = gen_inp()
        self.choosed_calc = 0
        self.prev_lines = 0

    def ask(self, prompt):
        if self.prev_lines > 0:
            print(f"\033[{self.prev_lines}F\033[J", end="")
        print(prompt)
        ans = input("입력 : ")
        self.prev_lines = prompt.count("\n") + 2 
        return ans

    def ask_yn(self, prompt):
        ans = self.ask(prompt)
        while ans not in ("y", "n"):
            ans = self.ask("제대로 쓰십시오 (y 또는 n)\n" + prompt)
        return ans

    def mol_chooser(self):
        status = 1
        while status:
            chk = self.ask_yn("xyz파일이 별도로 존재합니까? [y/n]")
            if chk == "y":
                xyz_files = glob.glob("*.xyz")
                if not xyz_files:
                    print("현재 폴더에 구조 정보를 가져올 .xyz 파일이 없습니다.")
                    continue
                else:
                    prompt = "구조 정보를 가져올 .xyz 파일을 선택하시오\n"
                    prompt += "\n".join(f"{i}. {xyz_files[i]}" for i in range(len(xyz_files)))
                    idx = int(self.ask(prompt))
                    chosen_inp = xyz_files[idx]
                    self.geninp.molname = chosen_inp[:-4]
                    status = 0
            elif chk == "n":
                chk = self.ask_yn("별도의 inp파일의 분자구조를 이용하시겠습니까?? [y/n]")
                if chk == "y":
                # [수정] *.xyz 대신 *.inp 파일 검색 및 내부 좌표 블록 추출 로직
                    inp_files = glob.glob("*.inp")
                    if not inp_files:
                        print("현재 폴더에 구조 정보를 가져올 .inp 파일이 없습니다.")
                        continue
                        
                    prompt = "구조 정보를 가져올 .inp 파일을 선택하시오\n"
                    prompt += "\n".join(f"{i}. {inp_files[i]}" for i in range(len(inp_files)))
                    idx = int(self.ask(prompt))
                    chosen_inp = inp_files[idx]
                    self.geninp.molname = chosen_inp[:-4]
                    
                    # 선택한 .inp 파일 열어서 xyz 블록 찾기
                    in_xyz = False
                    with open(chosen_inp, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        
                    for line in lines:
                        line_strip = line.strip().lower()
                        if line_strip.startswith("* xyzfile") or line_strip.startswith("*xyzfile"):
                            parts = line.strip().split()
                            if len(parts) >= 4:
                                self.geninp.xyz_file_ref = parts[-1]
                            break
                        elif line_strip.startswith("* xyz") or line_strip.startswith("*xyz"):
                            in_xyz = True
                        elif in_xyz:
                            if line.strip() == "*":
                                break
                            self.geninp.coords_lines.append(line)
                    status = 0
                if chk == "n":
                    continue

    def inp_chooser(self):
        inp_files = glob.glob("*.inp")
        prompt = "불러올 inp 파일을 선택하시오\n"
        prompt += "\n".join(f"{i}. {inp_files[i]}" for i in range(len(inp_files)))
        idx = int(self.ask(prompt))
        self.geninp.file_text = inp_files[idx]

    def calc_chooser(self):
        prompt = "원하는 계산을 선택해주세요\n0. DFT single point\n1. DFT opt\n2. TDDFT single point\n3. TDDFT opt\n4. DFT single Freq\n5. TDDFT Numfreq\n6. ESD\n7. SOCME\n8. NACME\n9. import inp"
        while True:
            self.geninp.calc = int(self.ask(prompt))
            if self.geninp.calc == 6 and not glob.glob("*.hess"): 
                self.ask("Hess 없음! 엔터를 누르면 계산 선택으로 돌아갑니다")
                continue
            break

    def common_chooser(self):
        self.geninp.functional = int(self.ask("choose functional\n0.HF 1.B3lyp 2.CAM-B3lyp 3.wB97x-d4 4.PBE 5.WB97X-2"))
        self.geninp.basis = int(self.ask("choose basis\n0.STO-3g 1.3-21G 2.6-31G 3.6-31G(d) \n4.6-31G(d,p) 5.def2-SVP 6.def2-TZVP 7.6-31++G(d,p)"))
        
        ans_c = self.ask("분자의 전하(Charge)를 입력하세요 (기본: 0, 양이온: 1, 음이온: -1)")
        self.geninp.charge = int(ans_c) if ans_c.strip() else 0
        
        ans_m = self.ask("분자의 스핀 다중도(Multiplicity)를 입력하세요 (단일항: 1, 삼중항: 3, 래디컬: 2 / 기본: 1)")
        self.geninp.mult = int(ans_m) if ans_m.strip() else 1

    def tddft_checker(self):
        if self.geninp.calc in (2, 3, 5, 6, 7, 8):
            self.geninp.nroots = int(self.ask("고려할 들뜬상태 개수(nroots)를 입력하세요"))
        if self.geninp.calc in (3, 5, 6, 8):
            self.geninp.iroot = int(self.ask("최적화/ESD/Numfreq/NACME 대상 들뜬상태 번호(iroot)를 입력하세요"))
        if self.geninp.calc == 2: 
            chk = self.ask_yn("삼중항(triplet) 상태도 같이 계산하시겠습니까? [y/n]")
            if chk == "y":
                self.geninp.triplets = 1
        if self.geninp.calc in (3, 5): 
            chk = self.ask_yn(f"iroot {self.geninp.iroot}번이 가리키는 상태가 삼중항(triplet)인가요? [y/n] (n이면 singlet)")
            if chk == "y":
                self.geninp.triplets = 1
                self.geninp.iroot_mult = 1
        if self.geninp.calc == 7:
            chk = self.ask_yn("SOC 전체 매트릭스/삼중항-삼중항 커플링까지 보고 싶으신가요? (PRINTLEVEL 3) [y/n]")
            if chk == "y":
                self.geninp.printlevel = 3

    def esd_checker(self):
        if self.geninp.calc == 6:
            self.geninp.esd_type = int(self.ask("ESD 종류를 선택하세요\n0. 형광(FLUOR)\n1. 흡수(ABS)\n2. 인광(PHOSP)"))
            self.geninp.gshess = self.ask("바닥상태 최적화 Hessian 파일명을 입력하세요 (예: gs.hess)")
            if self.geninp.esd_type == 2:
                self.geninp.tshess = self.ask("삼중항 최적화 Hessian 파일명을 입력하세요 (예: t1.hess)")
                self.geninp.dele = int(self.ask("바닥-삼중항 인접 에너지차 DELE(cm-1)를 입력하세요"))
            else:
                self.geninp.eshess = self.ask("들뜬상태 최적화 Hessian 파일명을 입력하세요 (예: s1.hess)")

            chk = self.ask_yn("Herzberg-Teller 효과(DOHT) 적용하시겠습니까? [y/n]")
            if chk == "y":
                self.geninp.doht = 1

            chk = self.ask_yn("Huang-Rhys factor 등 진동모드별 상세정보(PRINTLEVEL 3)까지 보고 싶으신가요? [y/n]")
            if chk == "y":
                self.geninp.printlevel = 3

    def approx_checker(self):
        if self.geninp.calc == 1:
            chk = self.ask_yn("RI-JK 적용 동의하십니까? [y/n]")
            if chk == "y":
                    self.geninp.rj = 1
        if self.geninp.calc in (2, 3, 5, 6, 7, 8):
            chk2 = self.ask_yn("TDA(Tamm-Dancoff) 근사 적용하시겠습니까? [y/n]")
            self.geninp.tda = 1 if chk2 == "y" else 0

    def tight_checker(self):
        # [수정] TDDFT 등에서 조건 분기하던 내용 삭제 (원래대로 모든 상황에서 질문)
        chk = self.ask_yn("타이트 적용 동의하십니까? [y/n]")
        if chk == "y":
            if self.geninp.calc != 9:
                self.geninp.tightscf = 1

    def spec_checker(self):
        if os.path.isfile("spec.txt"):
            with open("spec.txt", "r", encoding="utf-8") as f:
                cores, mem = f.read().split()
            self.geninp.cores = int(cores)
            self.geninp.mem = int(mem)
            chk = self.ask_yn(f"저장된 계산 사양(코어 {self.geninp.cores}, 코어당 메모리 {self.geninp.mem // 1000}GB)을 씁니다. 수정하시겠습니까? [y/n]")
            if chk == "y":
                self.geninp.cores = int(self.ask("코어수"))
                self.geninp.mem = int(self.ask("코어당 메모리(GB)")) * 1000
                with open("spec.txt", "w", encoding="utf-8") as f:
                    f.write(f"{self.geninp.cores} {self.geninp.mem}")
        else:
            chk = self.ask_yn("계산 사양 변경 원함??? [y/n]")
            if chk == "y":
                self.geninp.cores = int(self.ask("코어수"))
                self.geninp.mem = int(self.ask("코어당 메모리(GB)")) * 1000
                with open("spec.txt", "w", encoding="utf-8") as f:
                    f.write(f"{self.geninp.cores} {self.geninp.mem}")

    def run_checker(self):
        chk = self.ask_yn("지금 바로 ORCA로 실행하시겠습니까? [y/n]")
        if chk == "y":
            exc = excuter()
            if os.path.isfile("orca_pos.txt"):
                with open("orca_pos.txt", "r", encoding="utf-8") as f:
                    path = f.read().strip()
                if not os.path.isfile(path):
                    print("잘못된 경로!!!")
                    sys.exit(1)
                exc.orca_path = path
            else:
                path = self.ask("orca 실행파일 경로를 입력하세요 (엔터시 PATH에서 자동으로 찾음)")
                if path != "":
                    exc.orca_path = path
                else:
                    found = shutil.which("orca") 
                    if found:
                        exc.orca_path = found
                if os.path.isfile(exc.orca_path):
                    with open("orca_pos.txt", "w", encoding="utf-8") as f:
                        f.write(exc.orca_path)
            exc.run(self.geninp)

    def temp_main(self):
        self.calc_chooser()
        if self.geninp.calc == 9: 
            self.inp_chooser()
            self.geninp.text_load()
        else:
            self.mol_chooser()
            self.common_chooser()
            self.tddft_checker()
            self.esd_checker()
            self.approx_checker()
            self.tight_checker()
            self.spec_checker()
            self.geninp.gen_text()
            self.geninp.text_save()
        self.prev_lines = 0 
        self.run_checker()

class excuter:
    opt_cycle_re = re.compile(r"GEOMETR\w*\s+OPTIMIZATION CYCLE\s+(\d+)", re.IGNORECASE)
    scf_converged_re = re.compile(r"SCF CONVERGED AFTER\s+(\d+)\s+CYCLES", re.IGNORECASE)
    total_time_re = re.compile(r"TOTAL RUN TIME:\s*(.+)")
    final_energy_re = re.compile(r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)")

    def __init__(self):
        self.orca_path = "orca"

    def run(self, geninp):
        inp_path = geninp.file_text
        out_path = inp_path[:-4] + ".out"

        print(f"ORCA 실행: {self.orca_path} {inp_path} > {out_path}")

        status_len = [0]
        def status(msg): 
            pad = " " * max(0, status_len[0] - len(msg))
            print("\r" + msg + pad, end="", flush=True)
            status_len[0] = len(msg)

        with open(out_path, "w", encoding="utf-8") as out_f:
            proc = subprocess.Popen(
                [self.orca_path, inp_path],
                stdout=out_f,
                stderr=subprocess.STDOUT,
            )

            scf_count = 0
            last_opt_cycle = 0
            cycle_times = []
            last_cycle_ts = time.time()
            in_tddft = False

            with open(out_path, "r", encoding="utf-8") as f:
                while True:
                    line = f.readline()
                    if not line:
                        if proc.poll() is not None:
                            break
                        time.sleep(1)
                        continue

                    m = self.scf_converged_re.search(line)
                    if m:
                        scf_count += 1
                        status(f"[SCF] {scf_count}번째 SCF 계산 수렴 완료 ({m.group(1)} cycles)")

                    m = self.opt_cycle_re.search(line)
                    if m:
                        cyc = int(m.group(1))
                        if cyc > last_opt_cycle:
                            now = time.time()
                            if last_opt_cycle > 0:
                                cycle_times.append(now - last_cycle_ts)
                            last_cycle_ts = now
                            last_opt_cycle = cyc
                            if cycle_times:
                                avg = sum(cycle_times) / len(cycle_times)
                                status(f"[OPT] {cyc}번째 geometry 최적화 사이클 진행 중 (사이클당 평균 {avg:.1f}초, 참고용 추정치)")
                            else:
                                status(f"[OPT] {cyc}번째 geometry 최적화 사이클 진행 중")

                    if (not in_tddft) and ("TD-DFT" in line or "TDDFT" in line) and "CALCULATION" in line.upper():
                        in_tddft = True
                        status("[TDDFT] TDDFT 계산 진행 중...")

                    if "THE OPTIMIZATION HAS CONVERGED" in line:
                        status("[OPT] geometry 최적화 수렴 완료")

                    if "ORCA TERMINATED NORMALLY" in line:
                        status("[완료] ORCA TERMINATED NORMALLY")

            proc.wait()

        print() 

        self.summary(out_path)
        return proc.returncode

    def summary(self, out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            text = f.read()

        print("\n===== 계산 요약 =====")
        if "ORCA TERMINATED NORMALLY" in text:
            print("상태 : 정상 종료")
        else:
            print("상태 : 비정상 종료 (out 파일에서 에러 확인 필요)")

        m = self.total_time_re.search(text)
        if m:
            print(f"총 소요시간 : {m.group(1).strip()}")

        m = self.final_energy_re.search(text)
        if m:
            print(f"최종 에너지 : {m.group(1)} Eh")

        scf_matches = self.scf_converged_re.findall(text)
        print(f"SCF 계산 횟수 : {len(scf_matches)}")

        opt_matches = self.opt_cycle_re.findall(text)
        if opt_matches:
            print(f"geometry 최적화 사이클 수 : {opt_matches[-1]}")
        print("=====================\n")

chs = chooser()
chs.temp_main()
