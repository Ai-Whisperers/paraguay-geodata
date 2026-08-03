/* lang-switcher.js — small inline helper that builds the language
 * switcher in the lang-slot. Lives in a separate file so the home page
 * can be served with a strict CSP (no 'unsafe-inline').
 */
(function () {
  var slot = document.getElementById("lang-slot");
  if (slot && window.PY_I18N && window.PY_I18N.buildLangSwitcher) {
    window.PY_I18N.buildLangSwitcher(slot);
  }
})();
