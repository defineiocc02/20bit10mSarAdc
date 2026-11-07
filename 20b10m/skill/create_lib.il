;;; create_lib.il —— 在 Virtuoso 中创建 CICC26_SAR 计划库
;;;
;;; 用法（CIW 命令行）：
;;;   load("/path/to/20b10m/skill/create_lib.il")
;;;   createCICC26Lib("/path/to/20b10m/cds")
;;;   createCICC26Lib("/path/to/20b10m/cds" "smic18")     ; 同时挂 tech library
;;;
;;; 说明：
;;;   1. 只建库 + 26 个空 cell（schematic / symbol 两个 view）。
;;;   2. 引脚不在这里建 —— 由 verilogIn 导入 ../verilog/20b10m_skeleton.v 生成，
;;;      这样 pin 的方向/位宽与 spec/interfaces.csv 严格一致。
;;;   3. 本脚本未在 Virtuoso 里实测（L0），首次运行请留意 CIW 报错。

procedure(createCICC26Lib(libPath @optional (techLib nil))
  (let (libName cells cell cv n)
    libName = "CICC26_SAR"

    (unless (isDir libPath)
      (system (strcat "mkdir -p " libPath))
    )

    if (ddGetObj libName) then
      (printf "[CICC26] 库已存在：%s\n" libName)
    else
      (ddCreateLib libName libPath)
      (printf "[CICC26] 已创建库 %s -> %s\n" libName libPath)
    )

    (when techLib
      (errset (techAttachTechFile (ddGetObj libName) techLib))
    )

    cells = list(
      "Sar20bTop" "Sar1Top" "CoarseAdc6b" "Dac1_11b" "SwSample5v" "Cmp1"
      "SarLogic1" "TriLevelDrv"
      "RingAmp3" "FiaA1" "AmpA2" "FiaA3"
      "Sar2Ct" "CincCouple" "Dac2_12b" "Dac2Replica" "Cmp2" "SarLogic2"
      "DigitalTop" "LsbRepeat8" "Sinc2Dec" "GainScale" "BitRecombine" "LmsCal"
      "BiasGen" "RefBuffer"
    )

    n = 0
    (foreach cell cells
      (unless (ddGetObj libName cell)
        (errset
          (progn
            cv = dbOpenCellViewByType libName cell "schematic" "schematic" "w")
            (when cv (dbSave cv) (dbClose cv))
            cv = dbOpenCellViewByType libName cell "symbol" "symbol" "w")
            (when cv (dbSave cv) (dbClose cv))
          )
          t
        )
        (setq n (add1 n))
      )
    )

    (printf "[CICC26] 新建单元：%d / %d\n" n (length cells))
    (printf "[CICC26] 下一步：File -> Import -> Verilog，导入 20b10m_skeleton.v 生成引脚\n")
    (printf "[CICC26] 引脚数应与此一致（见 spec/interfaces.csv 汇总）：\n")
    (printf "  Sar20bTop=14 Sar1Top=19 CoarseAdc6b=9 Dac1_11b=14 SwSample5v=7\n")
    (printf "  Cmp1=7 SarLogic1=9 TriLevelDrv=11 RingAmp3=10 FiaA1=9 AmpA2=8 FiaA3=9\n")
    (printf "  Sar2Ct=12 CincCouple=9 Dac2_12b=7 Dac2Replica=7 Cmp2=7 SarLogic2=10\n")
    (printf "  DigitalTop=10 LsbRepeat8=5 Sinc2Dec=5 GainScale=5 BitRecombine=6\n")
    (printf "  LmsCal=5 BiasGen=9 RefBuffer=10   总计 233\n")
    t
  )
)
