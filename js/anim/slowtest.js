/* slowtest: "Boat and lab tests are slow and cost a lot."
 * Boat goes out -> a gloved hand fills a bottle -> the bottle goes to the lab ->
 * waiting (clock, calendar, coins) while the lake turns green -> the result comes
 * back and the lake is already green: "Too late!".
 * Vanilla JS + inline SVG, no network. Mounts on every [data-anim="slowtest"].
 */
(function () {
	"use strict";
	var NAME = "slowtest";
	var END = 11.8; // seconds

	var CSS = [
		".a-slowtest-wrap{ position:relative; width:100%; max-width:1000px; margin:0 auto; }",
		".a-slowtest-wrap svg.a-slowtest-svg{ display:block; width:100%; height:auto; max-height:calc(50vh - 56px); max-height:calc(50dvh - 56px); margin:0 auto; font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif; }",
		"@media (max-height:820px) and (min-width:861px){ .a-slowtest-wrap svg.a-slowtest-svg{ max-height:calc(46vh - 50px); max-height:calc(46dvh - 50px); } }",
		".a-slowtest-bar{ text-align:center; margin-top:6px; }",
		".a-slowtest-btn{ font:700 clamp(16px,1.5vw,20px)/1 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif; background:#073e77; color:#fff; border:0; border-radius:999px; padding:10px 24px; cursor:pointer; box-shadow:0 3px 0 rgba(11,18,32,.25); }",
		".a-slowtest-btn:hover{ background:#0a4f97; }",
		".a-slowtest-btn:focus-visible{ outline:4px solid #fece00; outline-offset:2px; }",
		".a-slowtest-btn[aria-disabled='true']{ opacity:.55; cursor:default; }"
	].join("\n");

	var uid = 0;

	function injectCss() {
		if (document.getElementById("anim-" + NAME + "-css")) return;
		var s = document.createElement("style");
		s.id = "anim-" + NAME + "-css";
		s.textContent = CSS;
		document.head.appendChild(s);
	}

	/* ---------- small math helpers ---------- */
	function clamp(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
	function seg(t, a, b) { return clamp((t - a) / (b - a)); }
	function ease(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
	function lerp(a, b, k) { return a + (b - a) * k; }
	function hex(c) { return [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)]; }
	function mix(c1, c2, k) {
		var a = hex(c1), b = hex(c2);
		return "rgb(" + Math.round(lerp(a[0], b[0], k)) + "," + Math.round(lerp(a[1], b[1], k)) + "," + Math.round(lerp(a[2], b[2], k)) + ")";
	}
	function quad(p0, p1, p2, k) { // quadratic bezier point
		var u = 1 - k;
		return [u * u * p0[0] + 2 * u * k * p1[0] + k * k * p2[0], u * u * p0[1] + 2 * u * k * p1[1] + k * k * p2[1]];
	}

	/* Algae dots on the lake (panel 1 coords): x, y, r */
	var DOTS = [[70, 140, 7], [96, 160, 9], [128, 136, 6], [150, 176, 8], [182, 146, 7], [210, 168, 9], [84, 186, 6],
		[118, 190, 7], [168, 196, 6], [222, 136, 6], [60, 168, 6], [196, 188, 7], [140, 156, 5], [230, 190, 5]];
	/* Coin pile (lab coords): 3 + 2 + 1 */
	var COINS = [[156, 176], [184, 176], [212, 176], [170, 151], [198, 151], [184, 126]];

	function svgMarkup(p) {
		var i, dots = "", coins = "", ticks = "";
		for (i = 0; i < DOTS.length; i++) {
			dots += '<circle class="a-slowtest-dot" cx="' + DOTS[i][0] + '" cy="' + DOTS[i][1] + '" r="' + DOTS[i][2] + '" opacity="0"/>';
		}
		for (i = 0; i < COINS.length; i++) {
			coins += '<g class="a-slowtest-coin" opacity="0" transform="translate(' + COINS[i][0] + ',' + COINS[i][1] + ')">' +
				'<circle r="14" fill="#fece00" stroke="#a87b00" stroke-width="3"/>' +
				'<text y="6" text-anchor="middle" font-size="17" font-weight="800" fill="#7a5a00">$</text></g>';
		}
		for (i = 0; i < 12; i++) {
			var a = i * Math.PI / 6;
			ticks += '<circle cx="' + (31 * Math.sin(a)).toFixed(1) + '" cy="' + (-31 * Math.cos(a)).toFixed(1) + '" r="' + (i % 3 ? 2 : 3.5) + '" fill="#073e77"/>';
		}
		var bottleShape =
			'<rect x="96" y="20" width="48" height="22" rx="4" fill="#073e77"/>' +
			'<rect x="104" y="40" width="32" height="18" fill="#e5edf5" stroke="#5b7fa6" stroke-width="3"/>' +
			'<rect x="80" y="56" width="80" height="100" rx="14" fill="#e5edf5" stroke="#5b7fa6" stroke-width="4"/>';

		return '' +
		'<svg class="a-slowtest-svg" viewBox="0 0 960 330" role="img" aria-label="Testing by hand: a boat goes out, someone fills a bottle with lake water, and the bottle goes to a lab. We wait, and it costs a lot. While we wait, the lake turns green. When the result comes back, it is too late.">' +
		'<defs>' +
			'<marker id="' + p + 'arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#073e77"/></marker>' +
			'<clipPath id="' + p + 'clip1"><rect width="240" height="200" rx="22"/></clipPath>' +
			'<clipPath id="' + p + 'clip2"><rect width="240" height="200" rx="22"/></clipPath>' +
			'<clipPath id="' + p + 'clipB"><rect x="84" y="60" width="72" height="92" rx="10"/></clipPath>' +
		'</defs>' +

		/* ---- Panel 1: the lake and the boat ---- */
		'<g transform="translate(40,30)">' +
			'<rect width="240" height="200" rx="22" fill="#fff"/>' +
			'<g clip-path="url(#' + p + 'clip1)">' +
				'<rect class="a-slowtest-lake" x="0" y="112" width="240" height="88" fill="#cfe8f3"/>' +
				'<g class="a-slowtest-dots" fill="#3f7a1c">' + dots + '</g>' +
				'<path d="M0 98h36q10 0 12 14v88H0z" fill="#efe4c8"/>' +
				'<rect x="28" y="104" width="38" height="7" rx="2" fill="#8d6e4f"/>' +
				'<rect x="58" y="104" width="6" height="22" fill="#8d6e4f"/>' +
			'</g>' +
			'<rect class="a-slowtest-panel" width="240" height="200" rx="22" fill="none" stroke="#c9d6e3" stroke-width="3"/>' +
			'<g class="a-slowtest-wake" opacity="0" fill="none" stroke="#7fb3cf" stroke-width="4" stroke-linecap="round"><path d="M-34 116h24M-46 126h30"/></g>' +
			'<g class="a-slowtest-boat" transform="translate(68,0)">' +
				'<path d="M0 100h96l-15 24H15z" fill="#073e77"/>' +
				'<rect x="32" y="74" width="34" height="26" rx="4" fill="#fece00" stroke="#0b1220" stroke-width="3"/>' +
			'</g>' +
		'</g>' +

		/* ---- Panel 2: the bottle ---- */
		'<g transform="translate(360,30)">' +
			'<rect width="240" height="200" rx="22" fill="#fff"/>' +
			'<g clip-path="url(#' + p + 'clip2)"><g class="a-slowtest-strip" opacity="0">' +
				'<rect x="0" y="150" width="240" height="50" fill="#cfe8f3"/>' +
				'<path d="M0 150q15-7 30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0" fill="none" stroke="#7fb3cf" stroke-width="4"/>' +
			'</g></g>' +
			'<g class="a-slowtest-bottle">' +
				bottleShape +
				'<rect class="a-slowtest-bwater" clip-path="url(#' + p + 'clipB)" x="84" y="88" width="72" height="64" fill="#8fc9e3"/>' +
				'<g class="a-slowtest-bubbles" fill="#fff" opacity="0"><circle cx="102" r="4"/><circle cx="122" r="3"/><circle cx="140" r="4"/></g>' +
				'<g class="a-slowtest-glove" opacity="0">' +
					'<rect x="160" y="34" width="80" height="26" rx="6" fill="#073e77"/>' +
					'<rect x="148" y="32" width="18" height="30" rx="5" fill="#fff" stroke="#0b1220" stroke-width="2.5"/>' +
					'<rect x="112" y="30" width="42" height="34" rx="14" fill="#2a9d8f" stroke="#0b1220" stroke-width="2.5"/>' +
					'<rect x="96" y="31" width="28" height="9" rx="4.5" fill="#2a9d8f" stroke="#0b1220" stroke-width="2.5"/>' +
					'<rect x="94" y="41" width="30" height="9" rx="4.5" fill="#2a9d8f" stroke="#0b1220" stroke-width="2.5"/>' +
					'<rect x="96" y="51" width="28" height="9" rx="4.5" fill="#2a9d8f" stroke="#0b1220" stroke-width="2.5"/>' +
					'<rect x="118" y="22" width="22" height="11" rx="5.5" fill="#2a9d8f" stroke="#0b1220" stroke-width="2.5"/>' +
				'</g>' +
			'</g>' +
			'<rect class="a-slowtest-panel" width="240" height="200" rx="22" fill="none" stroke="#c9d6e3" stroke-width="3"/>' +
		'</g>' +

		/* ---- Panel 3: the lab ---- */
		'<g transform="translate(680,30)">' +
			'<rect width="240" height="200" rx="22" fill="#fff"/>' +
			'<g class="a-slowtest-flask" transform="translate(50,30) scale(2.1875)" color="#073e77">' +
				'<path d="M24 6h16v4h-3v14l15 26c2 4-1 8-5 8H17c-4 0-7-4-5-8l15-26V10h-3z" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/>' +
				'<path d="M17 44h30l4 7c1 2 0 3-2 3H15c-2 0-3-1-2-3z" fill="currentColor"/>' +
			'</g>' +
			'<g class="a-slowtest-clock" opacity="0" transform="translate(62,62)">' +
				'<circle r="40" fill="#fff" stroke="#073e77" stroke-width="5"/>' + ticks +
				'<line class="a-slowtest-hour" x1="0" y1="0" x2="0" y2="-17" stroke="#0b1220" stroke-width="6" stroke-linecap="round"/>' +
				'<line class="a-slowtest-min" x1="0" y1="0" x2="0" y2="-27" stroke="#0b1220" stroke-width="4" stroke-linecap="round"/>' +
				'<circle r="4.5" fill="#d7263d"/>' +
			'</g>' +
			'<g class="a-slowtest-cal" opacity="0">' +
				'<rect x="128" y="22" width="90" height="80" rx="8" fill="#fff" stroke="#0b1220" stroke-width="3"/>' +
				'<g fill="#c9d6e3"><rect x="140" y="52" width="18" height="16" rx="3"/><rect x="164" y="52" width="18" height="16" rx="3"/><rect x="188" y="52" width="18" height="16" rx="3"/><rect x="140" y="74" width="18" height="16" rx="3"/><rect x="164" y="74" width="18" height="16" rx="3"/><rect x="188" y="74" width="18" height="16" rx="3"/></g>' +
				'<g class="a-slowtest-page">' +
					'<rect x="129.5" y="42" width="87" height="58.5" rx="6" fill="#f6f1e6" stroke="#0b1220" stroke-width="2"/>' +
					'<g fill="#9fb3c8"><rect x="140" y="52" width="18" height="16" rx="3"/><rect x="164" y="52" width="18" height="16" rx="3"/><rect x="188" y="52" width="18" height="16" rx="3"/><rect x="140" y="74" width="18" height="16" rx="3"/><rect x="164" y="74" width="18" height="16" rx="3"/><rect x="188" y="74" width="18" height="16" rx="3"/></g>' +
				'</g>' +
				'<rect x="128" y="22" width="90" height="22" rx="8" fill="#d7263d" stroke="#0b1220" stroke-width="3"/>' +
				'<rect x="148" y="14" width="7" height="16" rx="3" fill="#0b1220"/><rect x="191" y="14" width="7" height="16" rx="3" fill="#0b1220"/>' +
			'</g>' +
			'<g class="a-slowtest-coins">' + coins + '</g>' +
			'<rect class="a-slowtest-panel" width="240" height="200" rx="22" fill="none" stroke="#c9d6e3" stroke-width="3"/>' +
		'</g>' +

		/* ---- Arrows and labels ---- */
		'<line x1="288" y1="130" x2="350" y2="130" stroke="#073e77" stroke-width="8" marker-end="url(#' + p + 'arrow)"/>' +
		'<line x1="608" y1="130" x2="670" y2="130" stroke="#073e77" stroke-width="8" marker-end="url(#' + p + 'arrow)"/>' +
		'<g font-size="30" font-weight="700" text-anchor="middle" fill="#0b1220">' +
			'<text x="160" y="280">Boat</text><text x="480" y="280">Bottle</text><text x="800" y="280">Lab</text>' +
		'</g>' +
		'<text class="a-slowtest-caption" x="480" y="318" font-size="24" font-weight="700" text-anchor="middle" fill="#d7263d">Slow · costs a lot · not very often</text>' +

		/* ---- Things that fly over the panels ---- */
		'<g class="a-slowtest-mini" opacity="0">' +
			'<rect x="-10" y="-30" width="20" height="9" rx="2" fill="#073e77"/>' +
			'<rect x="-7" y="-22" width="14" height="8" fill="#e5edf5" stroke="#5b7fa6" stroke-width="2"/>' +
			'<rect x="-17" y="-15" width="34" height="45" rx="7" fill="#e5edf5" stroke="#5b7fa6" stroke-width="2.5"/>' +
			'<rect x="-14" y="4" width="28" height="23" rx="5" fill="#8fc9e3"/>' +
		'</g>' +
		'<g class="a-slowtest-result" opacity="0">' +
			'<rect x="-20" y="-25" width="40" height="50" rx="5" fill="#fff" stroke="#0b1220" stroke-width="3"/>' +
			'<path d="M-11-13h22M-11-4h22M-11 5h12" stroke="#9fb3c8" stroke-width="4" stroke-linecap="round"/>' +
			'<circle cx="8" cy="14" r="6" fill="#3f7a1c"/>' +
		'</g>' +
		'<g class="a-slowtest-late" opacity="0" transform="translate(480,128)">' +
			'<g class="a-slowtest-latein">' +
				'<rect x="-172" y="-52" width="344" height="104" rx="22" fill="#fff" stroke="#d7263d" stroke-width="8"/>' +
				'<text y="24" text-anchor="middle" font-size="70" font-weight="800" fill="#d7263d">Too late!</text>' +
			'</g>' +
		'</g>' +
		'</svg>';
	}

	function mount(el) {
		if (!el || el.getAttribute("data-anim-mounted") === "1") return;
		el.setAttribute("data-anim-mounted", "1");
		injectCss();
		var p = "a-slowtest-" + (++uid) + "-";

		var wrap = document.createElement("div");
		wrap.className = "a-slowtest-wrap";
		wrap.innerHTML = svgMarkup(p) +
			'<div class="a-slowtest-bar"><button type="button" class="a-slowtest-btn">▶ Play</button></div>';
		el.innerHTML = "";
		el.appendChild(wrap);

		function q(c) { return wrap.querySelector(".a-slowtest-" + c); }
		function qa(c) { return wrap.querySelectorAll(".a-slowtest-" + c); }
		var panels = qa("panel"), lake = q("lake"), dots = qa("dot"), boat = q("boat"), wake = q("wake"),
			strip = q("strip"), bottle = q("bottle"), bwater = q("bwater"), bubbles = q("bubbles"),
			bubbleDots = bubbles.querySelectorAll("circle"), glove = q("glove"), mini = q("mini"),
			flask = q("flask"), clock = q("clock"), hour = q("hour"), minute = q("min"), cal = q("cal"),
			page = q("page"), coins = qa("coin"), result = q("result"), late = q("late"),
			latein = q("latein"), caption = q("caption"), btn = q("btn");

		function render(t) {
			var k, i, x, y, pt;

			/* caption: shown at the start (today's picture) and again at the end */
			caption.setAttribute("opacity", (t < 6 ? 1 - seg(t, 0, 0.4) : seg(t, 11.3, 11.7)).toFixed(3));

			/* which panel is "on" */
			var on = t <= 0 ? -1 : t <= 1.9 ? 0 : t <= 4.4 ? 1 : t <= 10.1 ? 2 : -1;
			for (i = 0; i < 3; i++) {
				var red = i === 0 && t >= 10.8;
				panels[i].setAttribute("stroke", red ? "#d7263d" : on === i ? "#073e77" : "#c9d6e3");
				panels[i].setAttribute("stroke-width", red ? 7 : on === i ? 5 : 3);
			}

			/* 1. the boat goes out */
			k = ease(seg(t, 0.3, 1.9));
			var bx = lerp(68, 128, k);
			boat.setAttribute("transform", "translate(" + bx.toFixed(1) + "," + (t > 0.3 && t < 1.9 ? Math.sin(t * 9) * 1.5 : 0).toFixed(1) + ")");
			wake.setAttribute("transform", "translate(" + bx.toFixed(1) + ",0)");
			wake.setAttribute("opacity", (t > 0.3 && t < 2.3 ? Math.min(seg(t, 0.3, 0.6), 1 - seg(t, 1.8, 2.3)) : 0).toFixed(3));

			/* 2. someone fills the bottle */
			var level = t < 0.4 ? 1 : t < 2.7 ? 0 : seg(t, 2.7, 3.7);
			var wOp = t <= 0 ? 1 : t < 0.4 ? 1 - seg(t, 0, 0.4) : 1;
			var h = 64 * level;
			bwater.setAttribute("y", (152 - h).toFixed(1));
			bwater.setAttribute("height", h.toFixed(1));
			bwater.setAttribute("opacity", wOp.toFixed(3));
			var gOp = Math.min(seg(t, 1.9, 2.2), 1 - seg(t, 4.1, 4.4));
			glove.setAttribute("opacity", gOp.toFixed(3));
			strip.setAttribute("opacity", gOp.toFixed(3));
			var dip = 36 * (ease(seg(t, 2.2, 2.7)) - ease(seg(t, 3.7, 4.2)));
			bottle.setAttribute("transform", "translate(0," + dip.toFixed(1) + ")");
			var bubOn = t > 2.7 && t < 3.8;
			bubbles.setAttribute("opacity", bubOn ? 1 : 0);
			if (bubOn) {
				for (i = 0; i < bubbleDots.length; i++) {
					y = 150 - ((t * 70 + i * 23) % (h > 8 ? h : 8));
					bubbleDots[i].setAttribute("cy", y.toFixed(1));
				}
			}

			/* 3. the bottle goes to the lab */
			k = ease(seg(t, 4.4, 5.8));
			pt = quad([480, 150], [640, 30], [800, 190], k);
			mini.setAttribute("opacity", t >= 4.4 ? 1 : 0);
			mini.setAttribute("transform", "translate(" + pt[0].toFixed(1) + "," + pt[1].toFixed(1) + ") rotate(" + (Math.sin(k * Math.PI) * 18).toFixed(1) + ") scale(" + (1 + 0.4 * Math.sin(k * Math.PI)).toFixed(3) + ")");

			/* 4. waiting at the lab: flask moves aside, clock + calendar + coins */
			k = ease(seg(t, 5.6, 6.2));
			flask.setAttribute("transform", "translate(" + lerp(50, 10, k).toFixed(1) + "," + lerp(30, 108, k).toFixed(1) + ") scale(" + lerp(2.1875, 1.3, k).toFixed(4) + ")");
			clock.setAttribute("opacity", k.toFixed(3));
			cal.setAttribute("opacity", k.toFixed(3));
			var wait = seg(t, 6.2, 10.0);
			minute.setAttribute("transform", "rotate(" + (ease(wait) * 360 * 5).toFixed(1) + ")");
			hour.setAttribute("transform", "rotate(" + (ease(wait) * 150).toFixed(1) + ")");
			var flip = 0;
			if (t > 6.3 && t < 9.8) {
				x = ((t - 6.3) / 0.7) % 1; // 5 flips
				flip = seg(x, 0, 0.6);
			}
			page.setAttribute("transform", "translate(0,42) scale(1," + (1 - flip).toFixed(3) + ") translate(0,-42)");
			page.setAttribute("opacity", (1 - flip * flip).toFixed(3));
			for (i = 0; i < coins.length; i++) {
				var c0 = 6.4 + i * 0.6, ck = seg(t, c0, c0 + 0.35);
				coins[i].setAttribute("opacity", ck > 0 ? 1 : 0);
				coins[i].setAttribute("transform", "translate(" + COINS[i][0] + "," + (COINS[i][1] - 60 * (1 - ease(ck))).toFixed(1) + ")");
			}

			/* 5. meanwhile the lake turns green */
			lake.setAttribute("fill", mix("#cfe8f3", "#7cb944", seg(t, 5.8, 10.0)));
			for (i = 0; i < dots.length; i++) {
				var d0 = 6.2 + i * 0.26, dk = seg(t, d0, d0 + 0.4);
				dots[i].setAttribute("opacity", dk.toFixed(3));
				dots[i].setAttribute("r", (DOTS[i][2] * dk).toFixed(2));
			}

			/* 6. the result comes back ... too late */
			k = ease(seg(t, 10.1, 11.0));
			pt = quad([855, 95], [560, -20], [245, 62], k);
			result.setAttribute("opacity", t >= 10.1 ? 1 : 0);
			result.setAttribute("transform", "translate(" + pt[0].toFixed(1) + "," + pt[1].toFixed(1) + ") rotate(" + (-8 * Math.sin(k * Math.PI)).toFixed(1) + ")");
			k = seg(t, 11.0, 11.4);
			late.setAttribute("opacity", k > 0 ? 1 : 0);
			var s = k < 1 ? lerp(1.7, 1, ease(k)) : 1;
			latein.setAttribute("transform", "rotate(-6) scale(" + s.toFixed(3) + ")");
			latein.setAttribute("opacity", Math.min(1, k * 2).toFixed(3));
		}

		var raf = 0, timer = 0, t0 = 0, state = "start"; // start | playing | done

		function setBtn(label, disabled) {
			btn.textContent = label;
			if (disabled) btn.setAttribute("aria-disabled", "true");
			else btn.removeAttribute("aria-disabled");
		}
		function stop() {
			if (raf) cancelAnimationFrame(raf);
			if (timer) clearTimeout(timer);
			raf = 0; timer = 0;
		}
		function reset() { stop(); state = "start"; render(0); setBtn("▶ Play", false); }
		function finish() { stop(); state = "done"; render(END); setBtn("↻ Replay", false); }
		/* Next frame by requestAnimationFrame; a slow timer backs it up in case a
		   browser holds back animation frames, so the story never stalls. */
		function schedule() {
			raf = requestAnimationFrame(tick);
			timer = setTimeout(tick, 120);
		}
		function tick() {
			stop();
			if (state !== "playing") return;
			var t = (performance.now() - t0) / 1000;
			if (t >= END) { finish(); return; }
			render(t);
			schedule();
		}
		function play() {
			if (state === "playing") return;
			var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
			if (reduce) { finish(); return; }
			stop();
			state = "playing";
			setBtn("▶ Playing…", true);
			render(0.0001);
			t0 = performance.now();
			schedule();
		}

		btn.addEventListener("click", function () { play(); btn.blur(); });
		btn.addEventListener("keydown", function (e) {
			if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") e.stopPropagation();
		});

		/* Reset when the deck leaves this slide. */
		var slide = el.closest ? el.closest(".slide") : null;
		if (slide && window.MutationObserver) {
			new MutationObserver(function () {
				if (!slide.classList.contains("active") && state !== "start") reset();
			}).observe(slide, { attributes: true, attributeFilter: ["class"] });
		}

		var mode = el.getAttribute("data-anim-mode");
		if (mode === "end") finish(); else reset();
		/* seek(t) shows one frame (seconds), for checking and screenshots. */
		var api = { play: play, reset: reset, finish: finish, duration: END,
			seek: function (t) { stop(); state = "done"; render(Math.max(0, Math.min(END, t))); setBtn("▶ Play", false); } };
		el.AF1AnimCtl = api;
		return api;
	}

	window.AF1Anim = window.AF1Anim || {};
	window.AF1Anim[NAME] = { mount: mount };

	function mountAll() {
		var els = document.querySelectorAll('[data-anim="' + NAME + '"]');
		for (var i = 0; i < els.length; i++) mount(els[i]);
	}
	if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountAll);
	else mountAll();
})();
