/**
 * Generates a synthetic medical laboratory report image on an HTML5 canvas
 * for instant one-click demonstration testing.
 */
export const generateSampleReportFile = (type = 'blood_panel') => {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas');
    canvas.width = 1000;
    canvas.height = 750;
    const ctx = canvas.getContext('2d');

    // White background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Header styling
    ctx.fillStyle = '#0f766e';
    ctx.fillRect(0, 0, canvas.width, 100);

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 28px sans-serif';
    ctx.fillText('METRO HEALTH DIAGNOSTICS & PATHOLOGY', 40, 48);
    ctx.font = '16px sans-serif';
    ctx.fillText('Comprehensive Laboratory Investigation Report', 40, 78);

    // Patient info banner (Synthetic mock data)
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(30, 120, 940, 90);
    ctx.strokeStyle = '#e2e8f0';
    ctx.strokeRect(30, 120, 940, 90);

    ctx.fillStyle = '#334155';
    ctx.font = 'bold 15px sans-serif';
    ctx.fillText('Patient Name: Alexander Wright', 50, 150);
    ctx.fillText('Patient ID: MH-849201', 50, 185);
    ctx.fillText('Age / Sex: 42 Y / Male', 380, 150);
    ctx.fillText('DOB: 18/09/1984', 380, 185);
    ctx.fillText('Phone: +1 555-019-2834', 700, 150);
    ctx.fillText('Referred By: Dr. S. Patel, MD', 700, 185);

    // Table Header
    const startY = 245;
    ctx.fillStyle = '#f1f5f9';
    ctx.fillRect(30, startY, 940, 40);
    ctx.fillStyle = '#0f172a';
    ctx.font = 'bold 14px sans-serif';
    ctx.fillText('INVESTIGATION / TEST NAME', 50, startY + 26);
    ctx.fillText('OBSERVED RESULT', 420, startY + 26);
    ctx.fillText('UNITS', 620, startY + 26);
    ctx.fillText('BIOLOGICAL REFERENCE INTERVAL', 720, startY + 26);

    // Table Rows
    const rows = [
      { name: 'Hemoglobin (Hb)', result: '14.2', unit: 'g/dL', range: '13.0 - 17.0', flag: 'Normal' },
      { name: 'Fasting Blood Glucose', result: '118', unit: 'mg/dL', range: '70 - 100', flag: 'High' },
      { name: 'Serum Creatinine', result: '1.05', unit: 'mg/dL', range: '0.70 - 1.30', flag: 'Normal' },
      { name: 'Total Cholesterol', result: '228', unit: 'mg/dL', range: '< 200', flag: 'High' },
      { name: 'HDL Cholesterol', result: '46', unit: 'mg/dL', range: '> 40', flag: 'Normal' },
      { name: 'Platelet Count', result: '240', unit: '10^3/uL', range: '150 - 450', flag: 'Normal' },
      { name: 'Total Bilirubin', result: '0.8', unit: 'mg/dL', range: '0.2 - 1.2', flag: 'Normal' },
    ];

    let currentY = startY + 40;
    rows.forEach((row, i) => {
      ctx.fillStyle = i % 2 === 0 ? '#ffffff' : '#f8fafc';
      ctx.fillRect(30, currentY, 940, 42);

      ctx.strokeStyle = '#e2e8f0';
      ctx.strokeRect(30, currentY, 940, 42);

      ctx.fillStyle = '#1e293b';
      ctx.font = '14px sans-serif';
      ctx.fillText(row.name, 50, currentY + 26);

      ctx.font = 'bold 14px sans-serif';
      ctx.fillStyle = row.flag === 'High' ? '#b91c1c' : '#0f172a';
      ctx.fillText(row.result, 420, currentY + 26);

      ctx.font = '13px sans-serif';
      ctx.fillStyle = '#64748b';
      ctx.fillText(row.unit, 620, currentY + 26);
      ctx.fillText(row.range, 720, currentY + 26);

      currentY += 42;
    });

    // Medical disclaimer footer
    ctx.fillStyle = '#64748b';
    ctx.font = 'italic 11px sans-serif';
    ctx.fillText('Report verified by Pathologist. For clinical correlation with physician only.', 50, currentY + 40);

    canvas.toBlob((blob) => {
      const file = new File([blob], 'synthetic_sample_lab_report.png', { type: 'image/png' });
      resolve(file);
    }, 'image/png');
  });
};
