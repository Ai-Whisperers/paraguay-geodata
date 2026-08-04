/* exports/web/exports-csv.js — Bulk export of filtered listings to CSV / XLSX.
 *
 * Loaded lazily when the user clicks "Exportar CSV" on the Properties tab
 * (no Chrome-style site.css render-blocking for the bundle). Adds:
 *
 *   window.exportCSV(scope)            → triggers CSV download
 *   window.exportXLSX(scope)           → triggers XLSX download
 *   window.__propertiesToRows(features) → converts features to row objects
 *
 * Scope can be: 'filtered' | 'viewport' | 'selection'
 *
 * CSV columns (17): id, title, price_usd, price_pyg, area_ha, area_sqm,
 *  bedrooms, bathrooms, property_type, city, depto, barrio, currency,
 *  source, source_url, cluster_id, lat, lng.
 *
 * XLSX is a simpler CSV-in-XLSX format using a minimal ZIP writer — no
 * SheetJS dependency, no Excel.js. The .xlsx opens in Excel/LibreOffice/Numbers.
 */
(function () {
  "use strict";

  // ---------- Rows from features ----------
  function propertiesToRows(features) {
    if (!features) return [];
    return features.map((f) => {
      const p = (f.properties) || {};
      const coords = (f.geometry && f.geometry.coordinates) || [];
      const lon = coords[0];
      const lat = coords[1];
      const area_ha = +p.area_ha || 0;
      const area_sqm = +(area_ha * 10000).toFixed(2);
      return {
        id: p.id || "",
        title: p.title || "",
        price_usd: +p.price_usd || 0,
        price_pyg: +p.price_pyg || 0,
        area_ha: area_ha,
        area_sqm: area_sqm,
        bedrooms: +p.bedrooms || 0,
        bathrooms: +p.bathrooms || 0,
        property_type: p.property_type || "",
        city: p.city || "",
        depto: p.state_province || "",
        barrio: p.barrio || "",
        currency: p.currency || "",
        source: p.source || "",
        source_url: p.source_url || "",
        cluster_id: p.cluster_id || "",
        lat: lat != null ? +lat : "",
        lng: lon != null ? +lon : "",
      };
    });
  }

  // ---------- CSV ----------
  function csvEscape(value) {
    if (value == null) return "";
    const s = String(value);
    if (s.indexOf(",") === -1 && s.indexOf('"') === -1 && s.indexOf("\n") === -1 && s.indexOf("\r") === -1) {
      return s;
    }
    return '"' + s.replace(/"/g, '""') + '"';
  }

  function rowsToCSV(rows) {
    if (rows.length === 0) return "";
    const keys = Object.keys(rows[0]);
    const lines = [keys.join(",")];
    for (const row of rows) {
      lines.push(keys.map((k) => csvEscape(row[k])).join(","));
    }
    return lines.join("\r\n") + "\r\n";
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function getFeatures(scope) {
    scope = scope || "filtered";
    if (scope === "viewport" && typeof window.__exportInViewport === "function") {
      return window.__exportInViewport();
    }
    if (scope === "selection" && typeof window.__exportInSelection === "function") {
      return window.__exportInSelection();
    }
    if (typeof window.__exportGetFiltered === "function") {
      return window.__exportGetFiltered();
    }
    return [];
  }

  function showToast(msg, kind) {
    if (typeof window.showToast === "function") {
      window.showToast(msg, kind || "success");
    }
  }

  function exportCSV(scope) {
    const features = getFeatures(scope);
    if (!features || features.length === 0) {
      showToast("No hay propiedades para exportar en el alcance seleccionado.", "error");
      return;
    }
    const rows = propertiesToRows(features);
    const csv = rowsToCSV(rows);
    // Prepend BOM so Excel detects UTF-8 correctly with accented characters
    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
    const today = new Date().toISOString().slice(0, 10);
    downloadBlob(blob, `paraguay-properties-${scope}-${features.length}-${today}.csv`);
    showToast(`Descargado ${features.length.toLocaleString()} propiedades (CSV · ${scope})`, "success");
  }

  // ---------- XLSX (minimal pure-JS ZIP) ----------
  // We build a minimal XLSX file from scratch using JSZip-equivalent
  // uncompressed ZIP format. This avoids SheetJS (~150 KB) or Excel.js
  // (~200 KB) dependencies.
  function rowsToXLSX(rows) {
    const xml = [];
    // Sheet header
    xml.push('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>');
    xml.push('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">');
    xml.push('<sheetData>');
    if (rows.length === 0) {
      xml.push('</sheetData></worksheet>');
      return xml.join("");
    }
    const keys = Object.keys(rows[0]);
    // Header row
    xml.push('<row r="1">');
    keys.forEach((k, i) => {
      const col = String.fromCharCode(65 + i);
      xml.push(`<c r="${col}1" t="inlineStr"><is><t>${xmlEscape(k)}</t></is></c>`);
    });
    xml.push('</row>');
    // Data rows
    rows.forEach((row, rIdx) => {
      const rowNum = rIdx + 2;
      xml.push(`<row r="${rowNum}">`);
      keys.forEach((k, i) => {
        const col = String.fromCharCode(65 + i);
        const v = row[k];
        const cellRef = `${col}${rowNum}`;
        if (v == null || v === "") {
          // Skip empty cell
        } else if (typeof v === "number") {
          xml.push(`<c r="${cellRef}"><v>${v}</v></c>`);
        } else {
          xml.push(`<c r="${cellRef}" t="inlineStr"><is><t>${xmlEscape(String(v))}</t></is></c>`);
        }
      });
      xml.push('</row>');
    });
    xml.push('</sheetData></worksheet>');
    return xml.join("");
  }

  function xmlEscape(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&apos;");
  }

  // Minimal ZIP builder (uncompressed stored format)
  function crc32(buf) {
    let c;
    const table = [];
    for (let n = 0; n < 256; n++) {
      c = n;
      for (let k = 0; k < 8; k++) {
        c = ((c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1));
      }
      table[n] = c;
    }
    let crc = 0xFFFFFFFF;
    for (let i = 0; i < buf.length; i++) {
      crc = (crc >>> 8) ^ table[(crc ^ buf[i]) & 0xFF];
    }
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }

  function buildZip(entries) {
    // entries: [{name, content: Uint8Array}]
    const parts = [];
    const central = [];
    let offset = 0;
    for (const e of entries) {
      const nameBytes = new TextEncoder().encode(e.name);
      const crc = crc32(e.content);
      const size = e.content.length;
      // Local file header
      const lfh = new Uint8Array(30 + nameBytes.length);
      const lv = new DataView(lfh.buffer);
      lv.setUint32(0, 0x04034b50, true);   // signature
      lv.setUint16(4, 20, true);           // version
      lv.setUint16(6, 0, true);            // flags
      lv.setUint16(8, 0, true);            // compression (stored)
      lv.setUint16(10, 0, true);           // mod time
      lv.setUint16(12, 0, true);           // mod date
      lv.setUint32(14, crc, true);
      lv.setUint32(18, size, true);
      lv.setUint32(22, size, true);
      lv.setUint16(26, nameBytes.length, true);
      lv.setUint16(28, 0, true);           // extra length
      lfh.set(nameBytes, 30);
      parts.push(lfh);
      parts.push(e.content);
      // Central directory entry
      const cdh = new Uint8Array(46 + nameBytes.length);
      const cv = new DataView(cdh.buffer);
      cv.setUint32(0, 0x02014b50, true);   // signature
      cv.setUint16(4, 20, true);           // version made by
      cv.setUint16(6, 20, true);           // version needed
      cv.setUint16(8, 0, true);            // flags
      cv.setUint16(10, 0, true);           // compression
      cv.setUint16(12, 0, true);           // mod time
      cv.setUint16(14, 0, true);           // mod date
      cv.setUint32(16, crc, true);
      cv.setUint32(20, size, true);
      cv.setUint32(24, size, true);
      cv.setUint16(28, nameBytes.length, true);
      cv.setUint16(30, 0, true);           // extra length
      cv.setUint16(32, 0, true);           // comment length
      cv.setUint16(34, 0, true);           // disk
      cv.setUint16(36, 0, true);           // internal attrs
      cv.setUint32(38, 0, true);           // external attrs
      cv.setUint32(42, offset, true);      // local header offset
      cdh.set(nameBytes, 46);
      central.push(cdh);
      offset += lfh.length + e.content.length;
    }
    const cdSize = central.reduce((s, c) => s + c.length, 0);
    const cdOffset = offset;
    const eocd = new Uint8Array(22);
    const ev = new DataView(eocd.buffer);
    ev.setUint32(0, 0x06054b50, true);     // signature
    ev.setUint16(4, 0, true);              // disk
    ev.setUint16(6, 0, true);              // disk with cd
    ev.setUint16(8, entries.length, true); // entries on this disk
    ev.setUint16(10, entries.length, true);// total entries
    ev.setUint32(12, cdSize, true);
    ev.setUint32(16, cdOffset, true);
    ev.setUint16(20, 0, true);             // comment length
    const blobParts = parts.concat(central).concat([eocd]);
    return new Blob(blobParts, { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  }

  function utf8Bytes(s) {
    return new TextEncoder().encode(s);
  }

  function exportXLSX(scope) {
    const features = getFeatures(scope);
    if (!features || features.length === 0) {
      showToast("No hay propiedades para exportar en el alcance seleccionado.", "error");
      return;
    }
    const rows = propertiesToRows(features);
    const sheetXml = rowsToXLSX(rows);
    // [Content_Types].xml
    const contentTypes = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
      '<Default Extension="xml" ContentType="application/xml"/>' +
      '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' +
      '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' +
      '</Types>';
    const rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
      '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>' +
      '</Relationships>';
    const workbook = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' +
      '<sheets><sheet name="Propiedades" sheetId="1" r:id="rId1"/></sheets>' +
      '</workbook>';
    const blob = buildZip([
      { name: "[Content_Types].xml", content: utf8Bytes(contentTypes) },
      { name: "_rels/.rels", content: utf8Bytes(rels) },
      { name: "xl/workbook.xml", content: utf8Bytes(workbook) },
      { name: "xl/worksheets/sheet1.xml", content: utf8Bytes(sheetXml) },
    ]);
    const today = new Date().toISOString().slice(0, 10);
    downloadBlob(blob, `paraguay-properties-${scope}-${features.length}-${today}.xlsx`);
    showToast(`Descargado ${features.length.toLocaleString()} propiedades (XLSX · ${scope})`, "success");
  }

  // Expose
  window.exportCSV = exportCSV;
  window.exportXLSX = exportXLSX;
  window.__propertiesToRows = propertiesToRows;
})();