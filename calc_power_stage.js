// Power stage calculations script
const Vin = 36;
const Vout = 29;
const Iout = 18;
const Fsw = 200000;
const L = 6.8e-6;
const Dcr = 0.002;
const Rsense = 0.0025;

const D = Vout / Vin;
const deltaIL = ((Vin - Vout) * D) / (Fsw * L);
const IL_peak = Iout + deltaIL / 2;
const IL_rms = Math.sqrt(Iout * Iout + (deltaIL * deltaIL) / 12);
const P_L_cu = IL_rms * IL_rms * Dcr;

console.log('=== INDUCTOR L6 (MTP2915-6R8MC) ===');
console.log(`Duty Cycle D: ${(D * 100).toFixed(2)}%`);
console.log(`Ripple Current deltaIL: ${deltaIL.toFixed(3)} A (${((deltaIL / Iout) * 100).toFixed(1)}% ripple ratio)`);
console.log(`Peak Current IL_peak: ${IL_peak.toFixed(2)} A (Sat rating: 40A, margin: ${((1 - IL_peak / 40) * 100).toFixed(1)}%)`);
console.log(`RMS Current IL_rms: ${IL_rms.toFixed(2)} A (Rated: 30A, margin: ${((1 - IL_rms / 30) * 100).toFixed(1)}%)`);
console.log(`Inductor Copper Loss: ${P_L_cu.toFixed(3)} W`);

// MOSFETs
const Rds_hot = 0.0136; // 13.6mΩ at 100°C for single BSC070N10LS5
const Rds_pair = Rds_hot / 2; // 6.8mΩ

const I_hs_rms = Iout * Math.sqrt(D);
const P_hs_cond = I_hs_rms * I_hs_rms * Rds_pair;
const P_hs_sw = 0.5 * Vin * Iout * 20e-9 * Fsw; // 20ns tr+tf
const P_hs_tot_per_fet = (P_hs_cond + P_hs_sw) / 2;

const I_ls_rms = Iout * Math.sqrt(1 - D);
const P_ls_cond = I_ls_rms * I_ls_rms * Rds_pair;
const P_ls_rr = 46e-9 * Vin * Fsw;
const P_ls_tot_per_fet = (P_ls_cond + P_ls_rr) / 2;

console.log('\n=== POWER MOSFETS (BSC070N10LS5 x 4) ===');
console.log(`High-Side RMS current: ${I_hs_rms.toFixed(2)} A`);
console.log(`High-Side conduction loss (total): ${P_hs_cond.toFixed(3)} W`);
console.log(`High-Side switching loss (total): ${P_hs_sw.toFixed(3)} W`);
console.log(`High-Side loss per FET (Q1, Q2): ${P_hs_tot_per_fet.toFixed(3)} W`);

console.log(`Low-Side RMS current: ${I_ls_rms.toFixed(2)} A`);
console.log(`Low-Side conduction loss (total): ${P_ls_cond.toFixed(3)} W`);
console.log(`Low-Side body diode Qrr loss: ${P_ls_rr.toFixed(3)} W`);
console.log(`Low-Side loss per FET (Q5, Q6): ${P_ls_tot_per_fet.toFixed(3)} W`);

// INTVCC Drive
const Qg_tot = 4 * 20e-9; // 4 FETs * 20nC
const I_gate = Qg_tot * Fsw;
const P_intvcc = (Vin - 5.0) * I_gate;
console.log('\n=== INTVCC GATE DRIVE ===');
console.log(`Gate drive current: ${(I_gate * 1000).toFixed(2)} mA (LT3763 rated ~50mA)`);
console.log(`LT3763 INTVCC LDO power dissipation: ${P_intvcc.toFixed(3)} W`);

// Shunt Resistors R1 & R12
const P_r1 = Iout * Iout * Rsense;
const Iin = (Vout * Iout) / (0.96 * Vin);
const P_r12 = Iin * Iin * Rsense;
console.log('\n=== CURRENT SHUNT RESISTORS (2.5mΩ WSLP2512) ===');
console.log(`R1 (Output) power dissipation at 18A: ${P_r1.toFixed(3)} W (WSLP2512 rated 3W)`);
console.log(`R12 (Input) power dissipation at ${Iin.toFixed(2)}A: ${P_r12.toFixed(3)} W (WSLP2512 rated 3W)`);
