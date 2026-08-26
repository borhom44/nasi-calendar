/* Curated FAQ search + render. No LLM -- substring match over normalized
 * Arabic text (alef/ya variants unified, diacritics stripped) so a search
 * for "محرم" also matches "المحرم" and "مُحرَّم" alike. */
function normalizeArabic(s) {
  return s
    .replace(/[ً-ٰٟ]/g, "")     // strip tashkeel/diacritics
    .replace(/[إأآا]/g, "ا")
    .replace(/ى/g, "ي")
    .replace(/ة/g, "ه")
    .toLowerCase();
}

function renderFAQ(filterRaw) {
  const filter = normalizeArabic((filterRaw || "").trim());
  const list = $("faqList");
  list.innerHTML = "";
  let shown = 0;

  // Read per call, not captured: the language can change without a reload.
  const cats = faqCategories(LANG), entries = faqEntries(LANG);
  cats.forEach((catName, catIdx) => {
    const items = entries.filter(item => item.cat === catIdx && (
      !filter || normalizeArabic(item.q).includes(filter) || normalizeArabic(item.a).includes(filter)
    ));
    if (!items.length) return;
    const h = document.createElement("h3");
    h.className = "faq-cat";
    h.textContent = catName;
    list.appendChild(h);
    for (const item of items) {
      const det = document.createElement("details");
      det.className = "faq-item";
      det.innerHTML = `<summary>${item.q}</summary><p>${item.a}</p>`;
      list.appendChild(det);
      shown++;
    }
  });

  if (!shown) {
    list.innerHTML = `<p class="hint" style="margin:0;">لا توجد نتائج مطابقة.</p>`;
  }
}
