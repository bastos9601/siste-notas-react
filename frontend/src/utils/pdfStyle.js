// Estilo común para todos los PDFs (jsPDF + autotable)
export const BRAND_COLOR = [37, 99, 235]; // azul barra
export const LIGHT_BG = [245, 247, 250];
export const TEXT_DARK = [33, 33, 33];

// Convierte una URL de imagen a DataURL para usar con jsPDF
export async function fetchImageDataUrl(url) {
  if (!url) return null;
  const res = await fetch(url, { mode: 'cors' });
  const blob = await res.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

// Dibuja encabezado tipo barra azul con título y subtítulo (opcional logo)
export function drawHeader(doc, { title = 'Sistema de Notas', subtitle = '', logoDataUrl = null }) {
  const pageWidth = doc.internal.pageSize.getWidth();
  doc.setFillColor(...BRAND_COLOR);
  doc.rect(0, 0, pageWidth, 28, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(16);
  doc.text(title, 14, 12);
  if (subtitle) {
    doc.setFontSize(11);
    doc.text(subtitle, 14, 20);
  }
  // Si hay logo, dibujarlo en la esquina superior derecha del encabezado
  if (logoDataUrl) {
    try {
      const format = (logoDataUrl.startsWith('data:image/jpeg') || logoDataUrl.startsWith('data:image/jpg')) ? 'JPEG' : 'PNG';
      const logoW = 36; // ancho en pt
      const logoH = 20; // alto en pt
      const x = pageWidth - 14 - logoW; // margen derecho de 14
      const y = 4; // dentro de la barra
      doc.addImage(logoDataUrl, format, x, y, logoW, logoH);
    } catch (e) {
      // Si falla el dibujado del logo, continuar sin interrumpir
      // console.warn('No se pudo insertar el logo en el PDF:', e);
    }
  }
  return 28; // altura usada por el header
}

// Dibuja líneas informativas y separador inferior
export function drawInfoWithSeparator(doc, lines, startY = 28) {
  const pageWidth = doc.internal.pageSize.getWidth();
  doc.setTextColor(...TEXT_DARK);
  doc.setFontSize(11);
  let y = startY;
  lines.forEach((t) => { doc.text(String(t), 14, y); y += 6; });
  doc.setDrawColor(200, 200, 200);
  doc.line(14, y + 4, pageWidth - 14, y + 4);
  return y + 6 + 4; // siguiente Y tras separador
}

// Opciones de tema por defecto para autoTable
export function autoTableTheme() {
  return {
    styles: { fontSize: 10, cellPadding: 3, textColor: TEXT_DARK },
    headStyles: { fillColor: BRAND_COLOR, textColor: 255, fontStyle: 'bold' },
    alternateRowStyles: { fillColor: LIGHT_BG },
    theme: 'grid',
  };
}

// Footer común por página
export function drawFooter(doc, label = '© Sistema de Notas') {
  return (data) => {
    const pw = doc.internal.pageSize.getWidth();
    const ph = doc.internal.pageSize.getHeight();
    doc.setFontSize(9);
    doc.setTextColor(130, 130, 130);
    doc.text(`Página ${data.pageNumber}`, 14, ph - 10);
    doc.text(label, pw - 14, ph - 10, { align: 'right' });
  };
}