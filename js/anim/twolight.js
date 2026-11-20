/*
 * twolight — "The two-light trick" animation for bioglow-judging.html (slide 5b).
 * Three cups (green algae, blue-green algae, mud) sit in a dark underwater box next to
 * one light sensor and two lamps. Play: the blue lamp sweeps the cups (both algae glow red,
 * mud stays dark), then the orange lamp (green algae: small glow, blue-green: BIG glow,
 * mud: no glow), then everything folds into the two-row summary table.
 * Step buttons ("Blue light", "Orange light") replay one row for Q&A.
 *
 * Use: <div data-anim="twolight"></div>   (optional data-anim-mode="summary" starts on the end frame)
 * Vanilla JS + inline SVG, no network. Everything is prefixed a-twolight-.
 */
(function () {
	"use strict";
	var NAME = "twolight";
	var SVGNS = "http://www.w3.org/2000/svg";
	var uid = 0;

	/* ---------- timeline (seconds) ---------- */
	var T = {
		capOut: [0, 0.4],      // "Two lights. One sensor." fades away
		bOn: [0.4, 0.9],       // blue lamp turns on
		bSweep: [0.9, 2.5],    // blue beam sweeps across the cups
		bOff: [4.3, 4.8],      // blue lamp off, glows fade
		oOn: [4.8, 5.3],       // orange lamp on
		oSweep: [5.3, 6.9],    // orange beam sweeps
		morph: [8.6, 9.9],     // fold into the two-row summary
		cap2: [9.9, 10.5],     // summary line + yellow ring
		end: 11.0
	};
	var STEP_BLUE = { from: 0, to: 2.7 };
	var STEP_ORANGE_TO = 7.0;

	/* ---------- layout (viewBox 1000 x 450) ---------- */
	var COLS = [380, 620, 860];
	var SCENE_Y = 180, SCENE_LABEL_Y = 300;
	var ROW_A = { y: 118, s: 0.6, ly: 196 };  // summary row 1 (blue light)
	var ROW_B = { y: 298, s: 0.6, ly: 376 };  // summary row 2 (orange light)
	var BEAM_X0 = 236, BEAM_X1 = 978;
	var LAMP_X = 212;
	var LAMPS = {
		blue: { scene: [LAMP_X, 120], sum: [112, 112], text: "Blue light", fill: "#3b82f6", label: "#9cc3ff" },
		orange: { scene: [LAMP_X, 240], sum: [112, 292], text: "Orange light", fill: "#f28c28", label: "#ffb878" }
	};
	var SAMPLES = [
		{ name: "Green algae", fill: "#6aa832", speck: "#a6d96a" },
		{ name: "Blue-green algae", fill: "#2a9d8f", speck: "#86d8cc" },
		{ name: "Mud", fill: "#8d6e4f", speck: "#5e4630" }
	];
	// Glow per row, per sample: radius (scene units), opacity, label, label colour.
	var GLOW_A = [
		{ r: 95, o: 1, label: "Glows red", c: "#ff8a8a" },
		{ r: 95, o: 1, label: "Glows red", c: "#ff8a8a" },
		{ r: 0, o: 0, label: "No glow", c: "#c7d2de" }
	];
	var GLOW_B = [
		{ r: 66, o: 0.55, label: "Small glow", c: "#ffc2c2" },
		{ r: 125, o: 1, label: "Big glow!", c: "#ff7070", bold: true },
		{ r: 0, o: 0, label: "No glow", c: "#c7d2de" }
	];

	/* ---------- helpers ---------- */
	function clamp(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
	function lerp(a, b, k) { return a + (b - a) * k; }
	function ease(k) { return k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2; }
	function back(k) { var c1 = 1.9, c3 = c1 + 1; return k <= 0 ? 0 : 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); }
	function seg(t, s) { return clamp((t - s[0]) / (s[1] - s[0])); }
	function set(el, attrs) { for (var k in attrs) el.setAttribute(k, attrs[k]); }
	function mk(tag, attrs, parent) {
		var el = document.createElementNS(SVGNS, tag);
		if (attrs) set(el, attrs);
		if (parent) parent.appendChild(el);
		return el;
	}
	function txt(attrs, str, parent) { var t = mk("text", attrs, parent); t.textContent = str; return t; }
	function reduced() { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); }

	/* ---------- CSS (once) ---------- */
	function injectCSS() {
		if (document.getElementById("anim-" + NAME + "-css")) return;
		var css =
			".a-twolight-root{width:100%;max-width:1000px;margin:0 auto;}" +
			".a-twolight-root svg.a-twolight-svg{display:block;width:100%;height:auto;max-height:46vh;max-height:46dvh;margin:0 auto;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;}" +
			"@media (max-height:820px){.a-twolight-root svg.a-twolight-svg{max-height:42vh;max-height:42dvh;}}" +
			".a-twolight-bar{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin:8px auto 0;}" +
			".a-twolight-btn{font:700 clamp(16px,1.6vw,20px)/1 system-ui,-apple-system,Segoe UI,Roboto,Arial;display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:10px 18px;border-radius:999px;cursor:pointer;border:2px solid var(--blue,#073e77);background:#fff;color:var(--blue,#073e77);}" +
			".a-twolight-btn:hover{background:#eaf1f8;}" +
			".a-twolight-btn:focus-visible{outline:3px solid var(--yellow,#fece00);outline-offset:2px;}" +
			".a-twolight-btn.a-twolight-play{background:var(--blue,#073e77);color:#fff;min-width:8.2em;justify-content:center;}" +
			".a-twolight-btn.a-twolight-play:hover{background:#0a4f96;}" +
			".a-twolight-btn[aria-pressed=true]{background:#fff7d1;border-color:var(--watch,#e0a800);}" +
			".a-twolight-dot{display:inline-block;width:.85em;height:.85em;border-radius:50%;}";
		var st = document.createElement("style");
		st.id = "anim-" + NAME + "-css";
		st.textContent = css;
		document.head.appendChild(st);
	}

	/* ---------- build one instance ---------- */
	function mount(host) {
		if (!host || host.getAttribute("data-anim-mounted") === NAME) return;
		host.setAttribute("data-anim-mounted", NAME);
		injectCSS();
		var n = ++uid, P = "a-twolight-";
		host.innerHTML = "";
		var root = document.createElement("div");
		root.className = P + "root";
		host.appendChild(root);

		var svg = mk("svg", {
			viewBox: "0 0 1000 450", "class": P + "svg", role: "img",
			"aria-label": "Under blue light, green algae and blue-green algae both glow red, and mud does not glow. Under orange light, green algae glow a little, blue-green algae glow a lot, and mud still does not glow."
		}, root);

		/* defs: the deck's red #glow look, plus beam gradients */
		var defs = mk("defs", null, svg);
		var glowId = P + "glow-" + n;
		var g = mk("radialGradient", { id: glowId }, defs);
		mk("stop", { offset: "0", "stop-color": "#ff3b3b", "stop-opacity": ".95" }, g);
		mk("stop", { offset: ".6", "stop-color": "#ff3b3b", "stop-opacity": ".35" }, g);
		mk("stop", { offset: "1", "stop-color": "#ff3b3b", "stop-opacity": "0" }, g);
		function beamGrad(id, color) {
			var lg = mk("linearGradient", { id: id, gradientUnits: "userSpaceOnUse", x1: BEAM_X0, y1: 0, x2: BEAM_X1, y2: 0 }, defs);
			mk("stop", { offset: "0", "stop-color": color, "stop-opacity": ".6" }, lg);
			mk("stop", { offset: "1", "stop-color": color, "stop-opacity": ".16" }, lg);
		}
		beamGrad(P + "beamB-" + n, "#4f8ff7");
		beamGrad(P + "beamO-" + n, "#f7953a");
		var water = mk("linearGradient", { id: P + "water-" + n, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
		mk("stop", { offset: "0", "stop-color": "#0f3a5f" }, water);
		mk("stop", { offset: "1", "stop-color": "#061a2e" }, water);

		/* column headers (on cream, like the old table) */
		var hdr = mk("g", { "font-size": 30, "font-weight": 800, "text-anchor": "middle", fill: "#0b1220" }, svg);
		SAMPLES.forEach(function (s, i) { txt({ x: COLS[i], y: 32 }, s.name, hdr); });

		/* dark underwater box */
		mk("rect", { x: 16, y: 46, width: 968, height: 362, rx: 24, fill: "url(#" + P + "water-" + n + ")" }, svg);
		var bub = mk("g", { fill: "none", stroke: "rgba(255,255,255,.16)", "stroke-width": 3 }, svg);
		[[300, 80, 7], [318, 104, 4], [500, 72, 5], [742, 92, 6], [756, 70, 3], [952, 120, 5], [470, 380, 4], [960, 360, 6]].forEach(function (b) {
			mk("circle", { cx: b[0], cy: b[1], r: b[2] }, bub);
		});

		/* summary row bands (hidden until the end) */
		var bandA = mk("rect", { x: 24, y: 54, width: 952, height: 171, rx: 18, fill: "#3b82f6", opacity: 0 }, svg);
		var bandB = mk("rect", { x: 24, y: 233, width: 952, height: 167, rx: 18, fill: "#f28c28", opacity: 0 }, svg);

		/* beams (under the cups) */
		var beamB = mk("polygon", { fill: "url(#" + P + "beamB-" + n + ")", opacity: 0 }, svg);
		var beamO = mk("polygon", { fill: "url(#" + P + "beamO-" + n + ")", opacity: 0 }, svg);

		/* sensor device body, sensor eye */
		var device = mk("g", null, svg);
		mk("rect", { x: 28, y: 78, width: 222, height: 204, rx: 20, fill: "#1c3655", stroke: "#5b7fa6", "stroke-width": 3 }, device);
		mk("circle", { cx: LAMP_X, cy: 180, r: 21, fill: "#0b1220", stroke: "#94a3b8", "stroke-width": 4 }, device);
		var eyeRed = mk("circle", { cx: LAMP_X, cy: 180, r: 16, fill: "#ff3b3b", opacity: 0 }, device);
		mk("circle", { cx: LAMP_X - 6, cy: 174, r: 4, fill: "#fff", opacity: 0.8 }, device);
		txt({ x: 112, y: 188, "font-size": 24, "font-weight": 700, "text-anchor": "middle", fill: "#e5edf5" }, "Sensor", device);

		/* lamps (move to the row labels in the summary) */
		function lampNode(L) {
			var gg = mk("g", null, svg);
			var halo = mk("circle", { cx: 0, cy: 0, r: 38, fill: L.fill, opacity: 0 }, gg);
			mk("circle", { cx: 0, cy: 0, r: 22, fill: "#4b5563", stroke: "#94a3b8", "stroke-width": 3 }, gg);
			var core = mk("circle", { cx: 0, cy: 0, r: 22, fill: L.fill, opacity: 0 }, gg);
			var rays = mk("path", { d: "M32 0h20M28 -16l17 -9M28 16l17 9", stroke: L.fill, "stroke-width": 6, "stroke-linecap": "round", fill: "none", opacity: 0 }, gg);
			var label = txt({ "font-weight": 800, "text-anchor": "middle", fill: L.label }, L.text, svg);
			return { g: gg, halo: halo, core: core, rays: rays, label: label, L: L };
		}
		var lampB = lampNode(LAMPS.blue);
		var lampO = lampNode(LAMPS.orange);

		/* cups: one cell = glow (behind) + glass + liquid + front tint; label separate */
		function cell(i, glow) {
			var s = SAMPLES[i];
			var gg = mk("g", null, svg);
			var back = mk("circle", { cx: 0, cy: 10, r: 0, fill: "url(#" + glowId + ")", opacity: 0 }, gg);
			mk("path", { d: "M-46 -50L46 -50L38 48Q37 56 29 56L-29 56Q-37 56 -38 48Z", fill: "rgba(255,255,255,.12)" }, gg);
			mk("path", { d: "M-42 -16L42 -16L37 46Q36 52 29 52L-29 52Q-36 52 -37 46Z", fill: s.fill }, gg);
			var sp = mk("g", { fill: s.speck }, gg);
			[[-20, 4, 5], [12, 18, 6], [-6, 34, 4], [22, -2, 4], [-26, 26, 3]].forEach(function (d) { mk("circle", { cx: d[0], cy: d[1], r: d[2] }, sp); });
			var front = mk("circle", { cx: 0, cy: 18, r: 44, fill: "url(#" + glowId + ")", opacity: 0 }, gg);
			mk("path", { d: "M-46 -50L46 -50L38 48Q37 56 29 56L-29 56Q-37 56 -38 48Z", fill: "none", stroke: "#c9d8e6", "stroke-width": 4, "stroke-linejoin": "round" }, gg);
			mk("path", { d: "M-54 -50H54", stroke: "#c9d8e6", "stroke-width": 6, "stroke-linecap": "round" }, gg);
			var label = txt({ x: COLS[i], "text-anchor": "middle", "font-weight": glow.bold ? 800 : 700, fill: glow.c, opacity: 0 }, glow.label, svg);
			return { g: gg, back: back, front: front, label: label, glow: glow, cx: COLS[i] };
		}
		var rowA = [0, 1, 2].map(function (i) { return cell(i, GLOW_A[i]); });
		var rowB = [0, 1, 2].map(function (i) { return cell(i, GLOW_B[i]); });

		/* yellow ring around "Big glow!" + captions */
		var ring = mk("rect", { x: 520, y: 238, width: 200, height: 160, rx: 18, fill: "none", stroke: "#fece00", "stroke-width": 6, opacity: 0 }, svg);
		var cap1 = txt({ x: 500, y: 440, "text-anchor": "middle", "font-size": 30, "font-weight": 800, fill: "#073e77" }, "Two lights. One sensor.", svg);
		var cap2 = txt({ x: 500, y: 440, "text-anchor": "middle", "font-size": 30, "font-weight": 800, fill: "#073e77", opacity: 0 }, "Blue-green glows most under orange!", svg);

		/* ---------- controls ---------- */
		var bar = document.createElement("div");
		bar.className = P + "bar";
		root.appendChild(bar);
		function button(cls, html, label) {
			var b = document.createElement("button");
			b.type = "button";
			b.className = P + "btn " + cls;
			b.innerHTML = html;
			if (label) b.setAttribute("aria-label", label);
			b.addEventListener("keydown", function (e) {
				if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") e.stopPropagation();
			});
			bar.appendChild(b);
			return b;
		}
		var playBtn = button(P + "play", "▶︎ Play");
		var blueBtn = button(P + "step", '<span class="' + P + 'dot" style="background:#3b82f6"></span>Blue light', "Show blue light");
		var orangeBtn = button(P + "step", '<span class="' + P + 'dot" style="background:#f28c28"></span>Orange light', "Show orange light");
		blueBtn.setAttribute("aria-pressed", "false");
		orangeBtn.setAttribute("aria-pressed", "false");

		/* ---------- render the frame at time t ---------- */
		function placeCell(c, cy, s, gAmt, labOp, ly, fs, op, overshoot) {
			set(c.g, { transform: "translate(" + c.cx + " " + cy + ") scale(" + s + ")", opacity: op });
			var gl = c.glow;
			if (gl.r > 0) {
				var k = overshoot ? back(gAmt) : gAmt;
				set(c.back, { r: (gl.r * (0.45 + 0.55 * k)).toFixed(1), opacity: (gl.o * clamp(gAmt)).toFixed(3) });
				set(c.front, { opacity: (0.6 * gl.o * clamp(gAmt)).toFixed(3) });
			} else {
				set(c.back, { opacity: 0 }); set(c.front, { opacity: 0 });
			}
			set(c.label, { y: ly.toFixed(1), "font-size": fs.toFixed(1), opacity: (labOp * op).toFixed(3) });
		}
		function reach(sx, cx, span) { return clamp((sx - (cx - 50)) / span); }
		function beamPoints(ly, sx) {
			return BEAM_X0 + "," + (ly - 12) + " " + sx.toFixed(1) + ",76 " + sx.toFixed(1) + ",286 " + BEAM_X0 + "," + (ly + 12);
		}
		function placeLamp(lp, on, m) {
			var a = lp.L.scene, b = lp.L.sum;
			var x = lerp(a[0], b[0], m), y = lerp(a[1], b[1], m);
			set(lp.g, { transform: "translate(" + x.toFixed(1) + " " + y.toFixed(1) + ")" });
			set(lp.halo, { opacity: (0.35 * on).toFixed(3) });
			set(lp.core, { opacity: on.toFixed(3) });
			set(lp.rays, { opacity: on.toFixed(3) });
			// text: left of the lamp in the device, under the lamp in the summary
			set(lp.label, { x: lerp(102, 112, m).toFixed(1), y: lerp(y + 8, y + 60, m).toFixed(1), "font-size": lerp(22, 28, m).toFixed(1) });
		}

		var cur = 0;
		function render(t) {
			var m = ease(seg(t, T.morph));
			var bOff = ease(seg(t, T.bOff));
			var bOn = ease(seg(t, T.bOn)) * (1 - bOff);
			var oOn = ease(seg(t, T.oOn));
			placeLamp(lampB, Math.max(bOn, m), m);
			placeLamp(lampO, Math.max(oOn, m), m);
			set(device, { opacity: (1 - m).toFixed(3) });
			set(bandA, { opacity: (0.16 * m).toFixed(3) });
			set(bandB, { opacity: (0.34 * m).toFixed(3) }); // orange needs more strength than blue to read as orange on the dark box
			set(cap1, { opacity: (1 - ease(seg(t, T.capOut))).toFixed(3) });
			var c2 = ease(seg(t, T.cap2));
			set(cap2, { opacity: c2.toFixed(3) });
			set(ring, { opacity: c2.toFixed(3) });

			// beams
			var bsx = lerp(BEAM_X0, BEAM_X1, ease(seg(t, T.bSweep)));
			var osx = lerp(BEAM_X0, BEAM_X1, ease(seg(t, T.oSweep)));
			set(beamB, { points: beamPoints(LAMPS.blue.scene[1], bsx), opacity: (t > T.bSweep[0] ? 1 - bOff : 0).toFixed(3) });
			var oFade = 1 - ease(seg(t, [T.morph[0], T.morph[0] + 0.6]));
			set(beamO, { points: beamPoints(LAMPS.orange.scene[1], osx), opacity: (t > T.oSweep[0] ? oFade : 0).toFixed(3) });

			var seen = 0, i, c, gA;
			// row A: blue-light results
			for (i = 0; i < 3; i++) {
				c = rowA[i];
				if (t < T.bOff[1]) {
					gA = reach(bsx, c.cx, 130) * (1 - bOff);
					placeCell(c, SCENE_Y, 1, gA, reach(bsx, c.cx, 60) * (1 - bOff), SCENE_LABEL_Y, 34, 1, false);
					seen = Math.max(seen, gA * c.glow.o);
				} else if (t < T.morph[0]) {
					placeCell(c, SCENE_Y, 1, 0, 0, SCENE_LABEL_Y, 34, 0, false);
				} else {
					placeCell(c, ROW_A.y, ROW_A.s, 1, 1, ROW_A.ly, 28, ease(seg(t, [T.morph[0] + 0.4, T.morph[1]])), false);
				}
			}
			// row B: orange-light results
			for (i = 0; i < 3; i++) {
				c = rowB[i];
				if (t < T.bOff[1]) {
					placeCell(c, SCENE_Y, 1, 0, 0, SCENE_LABEL_Y, 34, 0, false);
				} else {
					var gB = t < T.morph[0] ? reach(osx, c.cx, 130) : 1;
					var lB = t < T.morph[0] ? reach(osx, c.cx, 60) : 1;
					placeCell(c, lerp(SCENE_Y, ROW_B.y, m), lerp(1, ROW_B.s, m), gB, lB, lerp(SCENE_LABEL_Y, ROW_B.ly, m), lerp(34, 28, m), 1, i === 1);
					seen = Math.max(seen, clamp(gB) * c.glow.o);
				}
			}
			set(eyeRed, { opacity: (0.9 * seen * (1 - m)).toFixed(3) });
			cur = t;
		}

		/* ---------- playback ---------- */
		var raf = 0;
		function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
		function playRange(a, b, done) {
			stop();
			if (reduced()) { render(b); if (done) done(); return; }
			var t0 = null;
			function frame(now) {
				if (t0 === null) t0 = now;
				var t = a + (now - t0) / 1000;
				if (t >= b) { raf = 0; render(b); if (done) done(); return; }
				render(t);
				raf = requestAnimationFrame(frame);
			}
			render(a);
			raf = requestAnimationFrame(frame);
		}
		function pressed(btn) {
			blueBtn.setAttribute("aria-pressed", btn === blueBtn ? "true" : "false");
			orangeBtn.setAttribute("aria-pressed", btn === orangeBtn ? "true" : "false");
		}
		function setPlayLabel(replay) { playBtn.textContent = replay ? "↺ Replay" : "▶︎ Play"; }

		playBtn.addEventListener("click", function () {
			playBtn.blur();
			pressed(null);
			setPlayLabel(false);
			playRange(0, T.end, function () { setPlayLabel(true); });
		});
		blueBtn.addEventListener("click", function () {
			blueBtn.blur();
			pressed(blueBtn);
			setPlayLabel(false);
			playRange(STEP_BLUE.from, STEP_BLUE.to);
		});
		orangeBtn.addEventListener("click", function () {
			orangeBtn.blur();
			pressed(orangeBtn);
			setPlayLabel(false);
			// From a lit blue frame, let the blue light fade out first; otherwise start dark.
			var from = (cur > T.bSweep[0] && cur <= T.bOff[0]) ? T.bOff[0] : T.oOn[0];
			playRange(from, STEP_ORANGE_TO);
		});

		var mode = (host.getAttribute("data-anim-mode") || "").toLowerCase();
		function reset() {
			stop();
			pressed(null);
			if (mode === "summary") { render(T.end); setPlayLabel(true); }
			else { render(0); setPlayLabel(false); }
		}
		reset();

		/* reset when the deck leaves this slide */
		var slide = host.closest ? host.closest(".slide") : null;
		if (slide && window.MutationObserver) {
			var wasActive = slide.classList.contains("active");
			new MutationObserver(function () {
				var on = slide.classList.contains("active");
				if (wasActive && !on) reset();
				wasActive = on;
			}).observe(slide, { attributes: true, attributeFilter: ["class"] });
		}

		var api = { play: function () { playBtn.click(); }, reset: reset, render: render, duration: T.end };
		host.aTwolight = api; // handy for testing: el.aTwolight.render(5)
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
