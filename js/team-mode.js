/*
  Team mode: a "Present" button for the team's own laptop.

  - Open any page once with ?team in the address (for example aifuture1.org/?team).
    This laptop's browser remembers it, and pages that load this script with
    data-present show a small "Present" button that opens the judging slides.
  - Open any page with ?team=off to forget it and hide the button again.

  This is a CONVENIENCE, NOT SECURITY. It only keeps the slides out of the public
  menus. Anyone who knows the address can still open bioglow-judging.html, and the
  site's code is public on GitHub. Nothing secret belongs on the slides.

  If the browser blocks storage (private window, strict settings), the button
  simply never appears.
*/
(function () {
	var KEY = "af1-team-mode";
	var SLIDES = "bioglow-judging.html";
	var script = document.currentScript;

	function save(on) {
		try {
			if (on) localStorage.setItem(KEY, "1");
			else localStorage.removeItem(KEY);
		} catch (e) { /* storage blocked: ignore */ }
	}
	function isOn() {
		try { return localStorage.getItem(KEY) === "1"; }
		catch (e) { return false; }
	}

	var m = /[?&]team(?:=([^&#]*))?(?:[&#]|$)/.exec(location.search);
	if (m) save(m[1] !== "off");

	if (!script || !script.hasAttribute("data-present") || !isOn()) return;

	function addButton() {
		var a = document.createElement("a");
		a.href = SLIDES;
		a.textContent = "Present";
		a.title = "Team only: open the judging slides";
		a.setAttribute("data-team-present", "");
		a.style.cssText = "position:fixed;right:14px;bottom:14px;z-index:50;padding:8px 14px;border-radius:999px;" +
			"background:#073e77;color:#fff;font:600 14px system-ui,-apple-system,Segoe UI,Roboto,Arial;" +
			"text-decoration:none;box-shadow:0 4px 16px rgba(7,62,119,.25);opacity:.85;";
		document.body.appendChild(a);
	}
	if (document.body) addButton();
	else document.addEventListener("DOMContentLoaded", addButton);
})();
