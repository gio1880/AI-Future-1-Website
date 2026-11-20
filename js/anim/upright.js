/* AF1 animation "upright": the SpectraFloat buoy rocks in waves and swings back upright.
 *
 *   <div class="visual" data-anim="upright" data-anim-mode="float"></div>    (slide 5a, Brian)
 *   <div class="visual" data-anim="upright" data-anim-mode="compare"></div>  (slide 6, Julisa)
 *
 * float   : waves tip the buoy; a "float point" (foam pushes up) and a "heavy point"
 *           (weights pull down, far below) appear; each time it tips it swings back. ~8 s.
 * compare : Before (tall, narrow, weights higher) and After Oct 22 (low, wide, weights at the
 *           bottom) in the same waves. Before rocks a lot, After rocks a little. ~10 s.
 *           Qualitative only: no angles or numbers.
 *
 * Physics: the buoy turns about its float point. Buoyancy (up) and weight (down) always act
 * straight up and down, so the arrows stay vertical while the buoy tilts; the heavy point sits
 * far below the float point, so its pull swings the bottom back under and the buoy rights itself.
 *
 * Vanilla JS + inline SVG, no network. Every class starts with "a-upright-".
 */
(function () {
	"use strict";

	var NAME = "upright";
	var P = "a-upright-";

	var CSS = [
		".a-upright-wrap{width:100%;max-width:1000px;margin:0 auto;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;}",
		".a-upright-wrap svg.a-upright-svg{display:block;width:100%;height:auto;max-height:50vh;max-height:50dvh;margin:0 auto;font-family:inherit;overflow:hidden;}",
		"@media (max-height:820px){.a-upright-wrap svg.a-upright-svg{max-height:46vh;max-height:46dvh;}}",
		".a-upright-bar{display:flex;justify-content:center;margin-top:8px;}",
		".a-upright-btn{font:inherit;font-weight:800;font-size:clamp(17px,1.7vw,24px);line-height:1;border:0;border-radius:12px;padding:12px 28px;background:#073e77;color:#fff;cursor:pointer;display:inline-flex;align-items:center;gap:12px;box-shadow:0 3px 0 rgba(11,18,32,.25);}",
		".a-upright-btn:hover{background:#0a4f97;}",
		".a-upright-btn:focus-visible{outline:4px solid #fece00;outline-offset:3px;}",
		".a-upright-btn[data-state=playing]{background:#5b7fa6;}",
		".a-upright-ico{display:inline-block;width:0;height:0;border-style:solid;border-width:.48em 0 .48em .8em;border-color:transparent transparent transparent currentColor;}",
		".a-upright-btn[data-state=done] .a-upright-ico,.a-upright-btn[data-state=playing] .a-upright-ico{display:none;}"
	].join("");

	function injectCss() {
		if (document.getElementById("anim-upright-css")) return;
		var s = document.createElement("style");
		s.id = "anim-upright-css";
		s.textContent = CSS;
		(document.head || document.documentElement).appendChild(s);
	}

	/* ---------- small helpers ---------- */
	function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
	function ramp(t, a, b) { var u = clamp01((t - a) / (b - a)); return u * u * (3 - 2 * u); }
	function r1(x) { return Math.round(x * 10) / 10; }
	function rect(x1, y1, x2, y2, extra) {
		return '<rect x="' + x1 + '" y="' + y1 + '" width="' + (x2 - x1) + '" height="' + (y2 - y1) + '" ' + (extra || "") + "/>";
	}
	/* A world point for a point (lx, ly) on a buoy at (px, py) turned by th radians (clockwise). */
	function toWorld(px, py, th, lx, ly) {
		var c = Math.cos(th), s = Math.sin(th);
		return [px + lx * c - ly * s, py + lx * s + ly * c];
	}
	/* Line from a fixed label point to a moving point, stopping `gap` short of it. */
	function setLeader(line, x1, y1, x2, y2, gap) {
		var dx = x2 - x1, dy = y2 - y1, d = Math.sqrt(dx * dx + dy * dy) || 1;
		var k = Math.max(0, d - (gap || 0)) / d;
		line.setAttribute("x1", r1(x1)); line.setAttribute("y1", r1(y1));
		line.setAttribute("x2", r1(x1 + dx * k)); line.setAttribute("y2", r1(y1 + dy * k));
	}

	/* A wave "kick": tips the buoy, then it swings back (a damped swing). The peak is
	   normalised to `deg` and timed to happen when the wave crest is under the buoy. */
	function makeSwing(deg, period, tau) {
		var w = 2 * Math.PI / period;
		var sPeak = Math.atan(w * tau) / w;
		var peak = Math.exp(-sPeak / tau) * Math.sin(w * sPeak);
		return { amp: deg / peak, w: w, tau: tau, lead: sPeak };
	}
	function tilt(sw, t, waves) {
		var th = 0;
		for (var k = 0; k < waves.length; k++) {
			var s = t - waves[k] + sw.lead;
			if (s > 0) th += sw.amp * Math.exp(-s / sw.tau) * Math.sin(sw.w * s);
		}
		return th;
	}

	/* Water surface height (SVG y) at local x. Crests travel left to right and reach x = 0 just after each wave time. */
	function surface(sea, x, t, env) {
		var y = sea.wl + 3 * Math.sin(x / 38 + t * 3.2);
		for (var k = 0; k < sea.waves.length; k++) {
			var xc = (t - sea.waves[k] - 0.2) * sea.v;   /* the crest is under the left side when the tilt peaks */
			var u = (x - xc) / sea.width;
			y -= sea.h * env * Math.exp(-u * u);
		}
		return y;
	}
	function waterPaths(sea, x0, x1, ox, t, env, bottom) {
		var pts = [];
		for (var x = x0; x <= x1 + 0.1; x += 10) pts.push(r1(x + ox) + " " + r1(surface(sea, x, t, env)));
		var line = "M" + pts.join(" L");
		return { line: line, fill: line + " L" + (x1 + ox) + " " + bottom + " L" + (x0 + ox) + " " + bottom + "Z" };
	}

	/* The buoy, drawn like the deck's #buoy symbol. Local origin = the point it turns about. */
	function buoyMarkup(b) {
		var foam = 'rx="12" fill="#f5d77a" stroke="#b8962e" stroke-width="3"';
		var g = "";
		g += rect(-12, b.stem[0], -4, b.stem[1], 'fill="#2e7d4f"');
		g += rect(4, b.stem[0], 12, b.stem[1], 'fill="#2e7d4f"');
		if (b.sensor) g += rect(14, b.sensor[0], 58, b.sensor[1], 'rx="4" fill="#1f2937"');
		g += rect(-b.wt[0], b.wt[1], b.wt[0], b.wt[2], 'rx="4" fill="#6b7280"');
		g += rect(-b.foam[1], b.foam[2], -b.foam[0], b.foam[3], foam);
		g += rect(b.foam[0], b.foam[2], b.foam[1], b.foam[3], foam);
		g += rect(-b.box[0], b.box[1], b.box[0], b.box[2], 'rx="10" fill="#e5edf5" stroke="#5b7fa6" stroke-width="4"');
		g += rect(-8, b.light[0], 8, b.lid[1], 'fill="#3b4b5e"');
		g += rect(-b.lid[0], b.lid[1], b.lid[0], b.lid[2], 'rx="4" fill="#3b4b5e"');
		g += '<circle cx="0" cy="' + b.light[0] + '" r="' + Math.round(b.light[1] * 1.8) + '" fill="#2e9e44" opacity=".25"/>';
		g += '<circle cx="0" cy="' + b.light[0] + '" r="' + b.light[1] + '" fill="#2e9e44" stroke="#0b1220" stroke-width="3"/>';
		return g;
	}

	/* A thick vertical arrow from (0,0), length len (negative = up), with a white outline. */
	function arrowMarkup(len, color) {
		var dir = len < 0 ? -1 : 1, tip = len, base = len - dir * 26;
		var shaft = '<line x1="0" y1="' + (dir * 16) + '" x2="0" y2="' + base + '" stroke-linecap="round" ';
		var head = '<path d="M-17 ' + base + " L0 " + tip + " L17 " + base + 'Z" stroke-linejoin="round" ';
		return shaft + 'stroke="#fff" stroke-width="17"/>' + head + 'fill="#fff" stroke="#fff" stroke-width="8"/>' +
			shaft + 'stroke="' + color + '" stroke-width="9"/>' + head + 'fill="' + color + '"/>';
	}

	/* ================= MODE: float ================= */
	function floatScene() {
		var W = 1000, H = 480, WL = 215, CX = 390;
		var BUOY = { foam: [70, 150, -50, 0], box: [75, -95, 10], lid: [85, -103, -93], light: [-135, 22],
			stem: [10, 220], sensor: [90, 118], wt: [55, 214, 236] };
		var PY = WL + 22;      /* float point: the middle of the float, just under the waterline */
		var HEAVY = 130;       /* heavy point: far below the float point, toward the weights */
		var waves = [2.2, 4.3, 6.3];
		var sea = { wl: WL, v: 300, h: 34, width: 90, waves: waves };
		var swing = makeSwing(20, 1.5, 0.7);
		var DUR = 8.2, END_A = 7.3;
		var q = {};

		var blue = "#073e77", red = "#d7263d";
		var markup =
			'<path class="' + P + 'wback" fill="#cfe8f3"/>' +
			'<g class="' + P + 'buoy">' + buoyMarkup(BUOY) + "</g>" +
			'<path class="' + P + 'wfront" fill="#cfe8f3" opacity=".45"/>' +
			'<path class="' + P + 'wline" fill="none" stroke="#7fb3cf" stroke-width="4" stroke-linejoin="round"/>' +
			/* part names (shown from the start) */
			'<g font-size="34" font-weight="800" fill="#0b1220" text-anchor="end">' +
				'<line class="' + P + 'lfoam" stroke="#0b1220" stroke-width="3"/>' +
				'<text x="215" y="140">Foam</text>' +
				'<line class="' + P + 'lwt" stroke="#0b1220" stroke-width="3"/>' +
				'<text x="250" y="473">Weights</text>' +
			"</g>" +
			/* float point */
			'<g class="' + P + 'fp" opacity="0">' +
				'<line class="' + P + 'lfp" stroke="' + blue + '" stroke-width="3" stroke-dasharray="8 6"/>' +
				'<g class="' + P + 'fpm">' + arrowMarkup(-88, blue) +
					'<circle r="15" fill="#fff" stroke="' + blue + '" stroke-width="7"/></g>' +
				'<text x="600" y="294" font-size="34" font-weight="800" fill="' + blue + '">Float point</text>' +
				'<text x="600" y="330" font-size="28" font-weight="600" fill="#233">pushes up</text>' +
			"</g>" +
			/* heavy point */
			'<g class="' + P + 'hp" opacity="0">' +
				'<line class="' + P + 'lhp" stroke="' + red + '" stroke-width="3" stroke-dasharray="8 6"/>' +
				'<g class="' + P + 'hpm">' + arrowMarkup(80, red) +
					'<circle r="19" fill="#fff" opacity=".9"/>' +
					'<path d="M-11 -11L11 11M11 -11L-11 11" stroke="' + red + '" stroke-width="7" stroke-linecap="round"/></g>' +
				'<text x="600" y="410" font-size="34" font-weight="800" fill="' + red + '">Heavy point</text>' +
				'<text x="600" y="446" font-size="28" font-weight="600" fill="#233">pulls down</text>' +
			"</g>" +
			/* end badge */
			'<g class="' + P + 'badge" opacity="0">' +
				'<rect x="680" y="28" width="300" height="66" rx="33" fill="#2e9e44"/>' +
				'<text x="830" y="72" font-size="32" font-weight="800" fill="#fff" text-anchor="middle">✓ Back upright!</text>' +
			"</g>";

		function bind(svg) {
			["wback", "wfront", "wline", "buoy", "lfoam", "lwt", "fp", "lfp", "fpm", "hp", "lhp", "hpm", "badge"].forEach(function (n) {
				q[n] = svg.querySelector("." + P + n);
			});
		}

		function render(t) {
			var env = 1 - ramp(t, END_A, DUR);
			var w = waterPaths(sea, -CX, W - CX, CX, t, env, H);
			q.wback.setAttribute("d", w.fill);
			q.wfront.setAttribute("d", w.fill);
			q.wline.setAttribute("d", w.line);

			var deg = Math.max(-30, Math.min(30, tilt(swing, t, waves))) * env;
			var th = deg * Math.PI / 180;
			var bob = (surface(sea, 0, t, env) - WL) * 0.5;
			var px = CX, py = PY + bob;
			q.buoy.setAttribute("transform", "translate(" + r1(px) + " " + r1(py) + ") rotate(" + r1(deg * 10) / 10 + ")");

			var foam = toWorld(px, py, th, -110, -25);
			setLeader(q.lfoam, 200, 150, foam[0], foam[1], 0);
			var wt = toWorld(px, py, th, -55, 225);
			setLeader(q.lwt, 258, 462, wt[0], wt[1], 0);

			q.fpm.setAttribute("transform", "translate(" + r1(px) + " " + r1(py) + ")");
			setLeader(q.lfp, 590, 284, px, py, 22);
			var hp = toWorld(px, py, th, 0, HEAVY);
			q.hpm.setAttribute("transform", "translate(" + r1(hp[0]) + " " + r1(hp[1]) + ")");
			setLeader(q.lhp, 590, 400, hp[0], hp[1], 24);

			q.fp.setAttribute("opacity", r1(ramp(t, 0.3, 0.8) * 100) / 100);
			q.hp.setAttribute("opacity", r1(ramp(t, 1.1, 1.6) * 100) / 100);
			q.badge.setAttribute("opacity", r1(ramp(t, 7.4, 7.9) * 100) / 100);
		}

		return {
			viewBox: "0 0 " + W + " " + H, dur: DUR, markup: markup, bind: bind, render: render,
			label: "Animation: our buoy SpectraFloat floats in waves. The foam ring at the waterline floats it and the weights hang far below. The float point (foam) pushes up and the heavy point (weights, far below) pulls down, so each time a wave tips the buoy it swings back upright."
		};
	}

	/* ================= MODE: compare ================= */
	function compareScene() {
		var W = 1000, H = 520, WL = 310, HALF = 230, BOTTOM = 512;
		var BEFORE = { foam: [36, 70, -55, 5], box: [42, -150, 10], lid: [50, -158, -150], light: [-182, 18],
			stem: [10, 150], wt: [34, 128, 146] };
		var AFTER = { foam: [58, 140, -44, 4], box: [62, -64, 12], lid: [70, -72, -64], light: [-96, 18],
			stem: [12, 160], wt: [48, 156, 178] };
		var waves = [1.5, 4.2, 6.9];
		var sea = { wl: WL, v: 260, h: 30, width: 75, waves: waves };
		var panels = [
			{ cx: 250, py: WL + 18, swing: makeSwing(26, 2.2, 1.3), b: BEFORE },  /* rocks a lot */
			{ cx: 750, py: WL + 20, swing: makeSwing(7, 1.2, 0.45), b: AFTER }    /* rocks a little */
		];
		var DUR = 10, END_A = 9.0;
		var q = {};
		var green = "#14532d";

		var markup = "";
		markup += '<line x1="500" y1="20" x2="500" y2="' + BOTTOM + '" stroke="#c9b98f" stroke-width="3" stroke-dasharray="10 8"/>';
		markup += '<g font-size="38" font-weight="800" text-anchor="middle">' +
			'<text x="250" y="46" fill="#233">Before</text>' +
			'<text x="750" y="46" fill="#2e9e44">After (Oct 22)</text></g>';
		panels.forEach(function (p, i) {
			markup += '<path class="' + P + "wback" + i + '" fill="#cfe8f3"/>' +
				'<g class="' + P + "buoy" + i + '">' + buoyMarkup(p.b) + "</g>" +
				'<path class="' + P + "wfront" + i + '" fill="#cfe8f3" opacity=".45"/>' +
				'<path class="' + P + "wline" + i + '" fill="none" stroke="#7fb3cf" stroke-width="4" stroke-linejoin="round"/>';
		});
		markup += '<g font-size="30" font-weight="800" fill="' + green + '" text-anchor="end">' +
			'<line class="' + P + 'lfoam" stroke="' + green + '" stroke-width="3"/>' +
			'<text x="992" y="222">Low, wide</text><text x="992" y="254">float</text>' +
			'<line class="' + P + 'lwt" stroke="' + green + '" stroke-width="3"/>' +
			'<text x="992" y="430">Weights</text><text x="992" y="462">at the bottom</text></g>';
		markup += '<g class="' + P + 'caps" opacity="0" font-size="30" font-weight="800" text-anchor="middle">' +
			'<text x="250" y="94" fill="#b91c1c">Rocks a lot</text>' +
			'<text x="750" y="94" fill="' + green + '">Rocks a little</text></g>';

		function bind(svg) {
			panels.forEach(function (p, i) {
				p.wback = svg.querySelector("." + P + "wback" + i);
				p.wfront = svg.querySelector("." + P + "wfront" + i);
				p.wline = svg.querySelector("." + P + "wline" + i);
				p.g = svg.querySelector("." + P + "buoy" + i);
			});
			q.lfoam = svg.querySelector("." + P + "lfoam");
			q.lwt = svg.querySelector("." + P + "lwt");
			q.caps = svg.querySelector("." + P + "caps");
		}

		function render(t) {
			var env = 1 - ramp(t, END_A, DUR);
			panels.forEach(function (p) {
				var w = waterPaths(sea, -HALF, HALF, p.cx, t, env, BOTTOM);
				p.wback.setAttribute("d", w.fill);
				p.wfront.setAttribute("d", w.fill);
				p.wline.setAttribute("d", w.line);
				p.deg = Math.max(-30, Math.min(30, tilt(p.swing, t, waves))) * env;
				p.th = p.deg * Math.PI / 180;
				p.y = p.py + (surface(sea, 0, t, env) - WL) * 0.5;
				p.g.setAttribute("transform", "translate(" + p.cx + " " + r1(p.y) + ") rotate(" + r1(p.deg * 10) / 10 + ")");
			});
			var a = panels[1];
			var f = toWorld(a.cx, a.y, a.th, 99, -44);
			setLeader(q.lfoam, 905, 262, f[0], f[1], 3);
			var wt = toWorld(a.cx, a.y, a.th, 48, 167);
			setLeader(q.lwt, 860, 470, wt[0], wt[1], 2);
			q.caps.setAttribute("opacity", r1(ramp(t, 2.4, 2.9) * 100) / 100);
		}

		return {
			viewBox: "0 0 " + W + " " + H, dur: DUR, markup: markup, bind: bind, render: render,
			label: "Animation: two buoys in the same waves. Before: tall and narrow, with the weights higher up, so it rocks a lot. After (Oct 22): a low, wide float and the weights at the very bottom, so it rocks only a little."
		};
	}

	/* ================= mount ================= */
	function reducedMotion() {
		return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
	}

	function mount(el) {
		if (!el || el.__aUpright) return el && el.__aUpright;
		injectCss();
		var mode = (el.getAttribute("data-anim-mode") || "float").toLowerCase() === "compare" ? "compare" : "float";
		var sc = mode === "compare" ? compareScene() : floatScene();

		el.innerHTML = "";
		var wrap = document.createElement("div");
		wrap.className = P + "wrap " + P + mode;
		wrap.innerHTML =
			'<svg class="' + P + 'svg" viewBox="' + sc.viewBox + '" role="img" xmlns="http://www.w3.org/2000/svg">' + sc.markup + "</svg>" +
			'<div class="' + P + 'bar"><button type="button" class="' + P + 'btn"><span class="' + P + 'ico" aria-hidden="true"></span><span class="' + P + 'txt">Play</span></button></div>';
		el.appendChild(wrap);
		var svg = wrap.querySelector("svg");
		svg.setAttribute("aria-label", sc.label);
		var btn = wrap.querySelector("button");
		var txt = wrap.querySelector("." + P + "txt");
		sc.bind(svg);

		var raf = 0, t0 = 0;
		function setState(s) {
			btn.setAttribute("data-state", s);
			txt.textContent = s === "done" ? "↻ Replay" : s === "playing" ? "Playing…" : "Play";
		}
		function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
		function frame(now) {
			var t = (now - t0) / 1000;
			if (t >= sc.dur) { raf = 0; sc.render(sc.dur); setState("done"); return; }
			sc.render(t);
			raf = requestAnimationFrame(frame);
		}
		function play() {
			stop();
			if (reducedMotion()) { sc.render(sc.dur); setState("done"); return; }
			setState("playing");
			t0 = performance.now();
			sc.render(0);
			raf = requestAnimationFrame(frame);
		}
		function reset() { stop(); sc.render(0); setState("idle"); }

		btn.addEventListener("click", function (e) {
			e.stopPropagation();
			play();
			btn.blur();
		});
		btn.addEventListener("keydown", function (e) {
			var k = e.key;
			if (k === "Enter" || k === " " || k === "Spacebar") e.stopPropagation();
		});

		var slide = el.closest ? el.closest(".slide") : null;
		if (slide && window.MutationObserver) {
			new MutationObserver(function () {
				if (!slide.classList.contains("active")) reset();
			}).observe(slide, { attributes: true, attributeFilter: ["class"] });
		}

		reset();
		/* seek(t): freeze on the frame at t seconds (for checking frames and for printouts). */
		function seek(t) { stop(); t = Math.max(0, Math.min(sc.dur, +t || 0)); sc.render(t); setState(t >= sc.dur ? "done" : "idle"); }
		var api = { play: play, reset: reset, seek: seek, mode: mode, duration: sc.dur };
		el.__aUpright = api;
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
