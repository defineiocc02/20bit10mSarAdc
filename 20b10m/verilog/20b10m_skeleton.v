// CICC26 计划工程 —— 端口桩（V1 + V2 交织模块）
// 由 spec/interfaces.csv 自动导出，勿手改

module Sar20bTop (VINP, VINN, VREFP, VREFN, VCM, CLK, RSTN, CAL_EN, DOUT, DOUT_RDY, MON, VDD5, VDD18, GND);
  input  VINP;
  input  VINN;
  input  VREFP;
  input  VREFN;
  input  VCM;
  input  CLK;
  input  RSTN;
  input  CAL_EN;
  output [20:0] DOUT;
  output DOUT_RDY;
  output [7:0] MON;
  inout  VDD5;
  inout  VDD18;
  inout  GND;
endmodule

module Sar1Top (VINP, VINN, VREFP, VREFN, VGND, VCM, PHI_S, PHI_C0, PHI_C1, PHI_RA, D1, D1_RDY, VRESP, VRESN, VTOPP, VTOPN, VDD5, VDD18, GND);
  input  VINP;
  input  VINN;
  input  VREFP;
  input  VREFN;
  input  VGND;
  input  VCM;
  input  PHI_S;
  input  PHI_C0;
  input  PHI_C1;
  input  PHI_RA;
  output [10:0] D1;
  output D1_RDY;
  output VRESP;
  output VRESN;
  inout  VTOPP;
  inout  VTOPN;
  inout  VDD5;
  inout  VDD18;
  inout  GND;
endmodule

module SdacPool18 (VINP, VINN, VREFP, VREFN, VCM, VGND, PHI_ACQ, PHI_CONV, D1, SLICE_SEL, VTOPP, VTOPN, VDD5, GND);
  input  VINP;
  input  VINN;
  input  VREFP;
  input  VREFN;
  input  VCM;
  input  VGND;
  input  [1:0] PHI_ACQ;
  input  [1:0] PHI_CONV;
  input  [10:0] D1;
  input  [4:0] SLICE_SEL;
  inout  VTOPP;
  inout  VTOPN;
  inout  VDD5;
  inout  GND;
endmodule

module SdacSlice (VINP, VINN, VREFP, VREFN, VCM, VGND, DIN, PHI_ACQ, PHI_CONV, VTOPP, VTOPN, VDD5, GND);
  input  VINP;
  input  VINN;
  input  VREFP;
  input  VREFN;
  input  VCM;
  input  VGND;
  input  [13:0] DIN;
  input  PHI_ACQ;
  input  PHI_CONV;
  inout  VTOPP;
  inout  VTOPN;
  inout  VDD5;
  inout  GND;
endmodule

module AcqTrackCtl (CLK, TP, EN_ACQ, HOLD, TRACK_VAL, VDD18, GND);
  input  CLK;
  output TP;
  output [1:0] EN_ACQ;
  output [1:0] HOLD;
  input  [10:0] TRACK_VAL;
  inout  VDD18;
  inout  GND;
endmodule

module CmpQ2 (VINP, VINN, CLK, OUTP, OUTN, VDD18, GND);
  input  VINP;
  input  VINN;
  input  CLK;
  output OUTP;
  output OUTN;
  inout  VDD18;
  inout  GND;
endmodule

module CoarseAdc6b (VINP, VINN, VREFP, VREFN, VCM, PHI_C0, D1_MSB, VDD18, GND);
  input  VINP;
  input  VINN;
  input  VREFP;
  input  VREFN;
  input  VCM;
  input  PHI_C0;
  output [10:5] D1_MSB;
  inout  VDD18;
  inout  GND;
endmodule

module Dac1_11b (VINP, VINN, VREFP, VREFN, VCM, VGND, D1, PHI_S, PHI_C1, VTOPP, VTOPN, VDD5, VDD18, GND);
  input  VINP;
  input  VINN;
  input  VREFP;
  input  VREFN;
  input  VCM;
  input  VGND;
  input  [10:0] D1;
  input  PHI_S;
  input  PHI_C1;
  inout  VTOPP;
  inout  VTOPN;
  inout  VDD5;
  inout  VDD18;
  inout  GND;
endmodule

module SwSample5v (VIN, VOUT, PHI_S, CKS, VDD5, VDD18, GND);
  input  VIN;
  output VOUT;
  input  PHI_S;
  input  CKS;
  inout  VDD5;
  inout  VDD18;
  inout  GND;
endmodule

module Cmp1 (VINP, VINN, CLK, OUTP, OUTN, VDD18, GND);
  input  VINP;
  input  VINN;
  input  CLK;
  output OUTP;
  output OUTN;
  inout  VDD18;
  inout  GND;
endmodule

module SarLogic1 (CMPP, CMPN, VALID, DONE, Q, P, N, VDD18, GND);
  input  CMPP;
  input  CMPN;
  input  VALID;
  output DONE;
  output [10:0] Q;
  output [10:0] P;
  output [10:0] N;
  inout  VDD18;
  inout  GND;
endmodule

module TriLevelDrv (VREF, VCM, VGND, VIN, SAM-, PI, NI, OUT, VDD5, VDD18, GND);
  input  VREF;
  input  VCM;
  input  VGND;
  input  VIN;
  input  SAM-;
  input  PI;
  input  NI;
  output OUT;
  inout  VDD5;
  inout  VDD18;
  inout  GND;
endmodule

module RaMux (VINA_P, VINA_N, VINB_P, VINB_N, PHI_SEL, VOUTP, VOUTN, VDD18, GND);
  input  VINA_P;
  input  VINA_N;
  input  VINB_P;
  input  VINB_N;
  input  PHI_SEL;
  output VOUTP;
  output VOUTN;
  inout  VDD18;
  inout  GND;
endmodule

module DynRefBuf (REF_IN, VREFP_PRE, SEL, EN, VREFP_OUT, VREFN_OUT, VDD5, GND);
  input  REF_IN;
  input  VREFP_PRE;
  input  SEL;
  input  EN;
  output VREFP_OUT;
  output VREFN_OUT;
  inout  VDD5;
  inout  GND;
endmodule

module RingAmp3 (VINP, VINN, VOUTP, VOUTN, VCM, PHI_RA, PHI_AZ, EN, VDD18, GND);
  input  VINP;
  input  VINN;
  output VOUTP;
  output VOUTN;
  input  VCM;
  input  PHI_RA;
  input  PHI_AZ;
  input  EN;
  inout  VDD18;
  inout  GND;
endmodule

module FiaA1 (VINP, VINN, VOUTP, VOUTN, VBP, VBN, PHI_AZ, VDD18, GND);
  input  VINP;
  input  VINN;
  output VOUTP;
  output VOUTN;
  input  VBP;
  input  VBN;
  input  PHI_AZ;
  inout  VDD18;
  inout  GND;
endmodule

module AmpA2 (VINP, VINN, VOUTP, VOUTN, VBP, VBN, VDD18, GND);
  input  VINP;
  input  VINN;
  output VOUTP;
  output VOUTN;
  input  VBP;
  input  VBN;
  inout  VDD18;
  inout  GND;
endmodule

module FiaA3 (VINP, VINN, VOUTP, VOUTN, VCP, VCN, PHI_RA, VDD18, GND);
  input  VINP;
  input  VINN;
  output VOUTP;
  output VOUTN;
  input  VCP;
  input  VCN;
  input  PHI_RA;
  inout  VDD18;
  inout  GND;
endmodule

module Sar2Ct (VRESP, VRESN, VREFP2, VREFN2, VCM, PHI_RA, PHI_C2, D2, DT, DONE2, VDD18, GND);
  input  VRESP;
  input  VRESN;
  input  VREFP2;
  input  VREFN2;
  input  VCM;
  input  PHI_RA;
  input  PHI_C2;
  output [11:0] D2;
  output [7:0] DT;
  output DONE2;
  inout  VDD18;
  inout  GND;
endmodule

module CincCouple (VINP, VINN, VOUTP, VOUTN, VREPP, VREPN, D2, VDD18, GND);
  input  VINP;
  input  VINN;
  output VOUTP;
  output VOUTN;
  input  VREPP;
  input  VREPN;
  input  [11:0] D2;
  inout  VDD18;
  inout  GND;
endmodule

module Dac2_12b (DIN, VREFP, VREFN, VCM, VTOP, VDD18, GND);
  input  [11:0] DIN;
  input  VREFP;
  input  VREFN;
  input  VCM;
  inout  VTOP;
  inout  VDD18;
  inout  GND;
endmodule

module Dac2Replica (DIN, VREFP, VREFN, VCM, VTOP, VDD18, GND);
  input  [11:0] DIN;
  input  VREFP;
  input  VREFN;
  input  VCM;
  inout  VTOP;
  inout  VDD18;
  inout  GND;
endmodule

module Cmp2 (VINP, VINN, CLK, OUTP, OUTN, VDD18, GND);
  input  VINP;
  input  VINN;
  input  CLK;
  output OUTP;
  output OUTN;
  inout  VDD18;
  inout  GND;
endmodule

module SarLogic2 (CMPP, CMPN, VALID, DONE, P, N, D2, DT, VDD18, GND);
  input  CMPP;
  input  CMPN;
  input  VALID;
  output DONE;
  output [11:0] P;
  output [11:0] N;
  output [11:0] D2;
  output [7:0] DT;
  inout  VDD18;
  inout  GND;
endmodule

module DigitalTop (D1, D2, DT, CLK, RSTN, CAL_EN, DOUT, RDY, VDD18, GND);
  input  [10:0] D1;
  input  [11:0] D2;
  input  [7:0] DT;
  input  CLK;
  input  RSTN;
  input  CAL_EN;
  output [20:0] DOUT;
  output RDY;
  inout  VDD18;
  inout  GND;
endmodule

module SliceShuffler (IDX, SEED, CAL_EN, DITHER, SEL, VDD18, GND);
  input  [4:0] IDX;
  input  [7:0] SEED;
  input  CAL_EN;
  input  [1:0] DITHER;
  output [4:0] SEL;
  inout  VDD18;
  inout  GND;
endmodule

module LsbRepeat8 (DT_IN, PHI_C2, DT_OUT, VDD18, GND);
  input  [7:0] DT_IN;
  input  PHI_C2;
  output [7:0] DT_OUT;
  inout  VDD18;
  inout  GND;
endmodule

module Sinc2Dec (DT, CLK, DO3, VDD18, GND);
  input  [7:0] DT;
  input  CLK;
  output [23:0] DO3;
  inout  VDD18;
  inout  GND;
endmodule

module GainScale (DIN, G_SEL, DOUT, VDD18, GND);
  input  [23:0] DIN;
  input  [3:0] G_SEL;
  output [23:0] DOUT;
  inout  VDD18;
  inout  GND;
endmodule

module BitRecombine (D1, D2, W2, DOUT, VDD18, GND);
  input  [10:0] D1;
  input  [11:0] D2;
  input  [15:0] W2;
  output [20:0] DOUT;
  inout  VDD18;
  inout  GND;
endmodule

module LmsCal (ERR, CAL_EN, COEF, VDD18, GND);
  input  [11:0] ERR;
  input  CAL_EN;
  output [15:0] COEF;
  inout  VDD18;
  inout  GND;
endmodule

module BiasGen (IREF, EN, VBP1, VBP2, VBN1, VBN2, VCM_OUT, VDD18, GND);
  input  IREF;
  input  EN;
  output VBP1;
  output VBP2;
  output VBN1;
  output VBN2;
  output VCM_OUT;
  inout  VDD18;
  inout  GND;
endmodule

module RefBuffer (VREF_IN, VREFP, VREFN, VREFP2, VREFN2, VCM, EN, VDD5, VDD18, GND);
  input  VREF_IN;
  output VREFP;
  output VREFN;
  output VREFP2;
  output VREFN2;
  output VCM;
  input  EN;
  inout  VDD5;
  inout  VDD18;
  inout  GND;
endmodule
