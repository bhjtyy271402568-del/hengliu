function ntcResistance(T_celsius, R25 = 100000, B = 3950) {
  const T_kelvin = T_celsius + 273.15;
  const T0_kelvin = 25 + 273.15;
  return R25 * Math.exp(B * (1 / T_kelvin - 1 / T0_kelvin));
}

function calcThermalCurve(R57_val, R58_val = 100000, Vref = 2.0, Rsense = 0.0025) {
  const temps = [25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110];
  const results = [];

  for (const T of temps) {
    const Rntc = ntcResistance(T);
    const Rdown = (R58_val * Rntc) / (R58_val + Rntc);
    const Vctrl2 = Vref * (Rdown / (R57_val + Rdown));
    // LT3763: Visp_isn = min(50mV, Vctrl2 / 20)
    const Visp_isn = Math.min(0.050, Vctrl2 / 20);
    const I_max = Visp_isn / Rsense; // with 2.5mΩ

    results.push({
      T,
      Rntc_k: (Rntc / 1000).toFixed(2),
      Rdown_k: (Rdown / 1000).toFixed(2),
      Vctrl2: Vctrl2.toFixed(3),
      I_max: I_max.toFixed(2)
    });
  }
  return results;
}

console.log('=== THERMAL DERATING WITH R57 = 20kΩ, R58 = 100kΩ ===');
console.table(calcThermalCurve(20000));

console.log('\n=== THERMAL DERATING WITH R57 = 7.5kΩ, R58 = 100kΩ ===');
console.table(calcThermalCurve(7500));

console.log('\n=== THERMAL DERATING WITH R57 = 5.1kΩ, R58 = 100kΩ ===');
console.table(calcThermalCurve(5100));

console.log('\n=== THERMAL DERATING WITH R57 = 4.3kΩ, R58 = 100kΩ ===');
console.table(calcThermalCurve(4300));
