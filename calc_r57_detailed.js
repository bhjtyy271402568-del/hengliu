function ntcResistance(T_celsius, R25 = 100000, B = 3950) {
  const T_kelvin = T_celsius + 273.15;
  const T0_kelvin = 25 + 273.15;
  return R25 * Math.exp(B * (1 / T_kelvin - 1 / T0_kelvin));
}

function solveTcrit(R57, Vcrit = 0.900, Vref = 2.000, R58 = 100000, R25 = 100000, B = 3950) {
  const Rdown_crit = (R57 * Vcrit) / (Vref - Vcrit);
  if (Rdown_crit >= R58) return null;
  const Rntc_crit = (R58 * Rdown_crit) / (R58 - Rdown_crit);
  const T0_k = 25 + 273.15;
  const invT = (1 / T0_k) + Math.log(Rntc_crit / R25) / B;
  const T_crit_c = (1 / invT) - 273.15;
  return { Rdown_crit, Rntc_crit, T_crit_c };
}

const r57_values = [20000, 10000, 7500];
const temps = [25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110];

const tableData = [];
for (const T of temps) {
  const Rntc = ntcResistance(T);
  const Rdown = (100000 * Rntc) / (100000 + Rntc);

  const row = {
    '温度 T': `${T} °C`,
    'NTC阻值': `${(Rntc / 1000).toFixed(1)} kΩ`,
    '并联阻抗': `${(Rdown / 1000).toFixed(1)} kΩ`
  };

  for (const r of r57_values) {
    const label = `${r/1000}kΩ`;
    const Vctrl2 = 2.0 * (Rdown / (r + Rdown));
    // LT3763 current limit by CTRL2 with Rsense = 2.5mΩ:
    // Visp_isn = min(50mV, Vctrl2 / 20)
    // I_lim = Visp_isn / 2.5mΩ = min(20A, 20 * Vctrl2)
    const I_lim = Math.min(20.0, 20.0 * Vctrl2);
    row[`V_CTRL2 (${label})`] = `${Vctrl2.toFixed(3)} V`;
    row[`限流上限 (${label})`] = `${I_lim.toFixed(2)} A`;
  }
  tableData.push(row);
}

console.log(JSON.stringify(tableData, null, 2));
