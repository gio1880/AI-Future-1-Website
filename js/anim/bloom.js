/* "What is a bloom?" animation for the BIOGLOW judging slides (AI Future 1).
   A clear lake with a few algae dots -> the dots multiply until the water is green ("Bloom!")
   -> SOME clusters get a warning mark -> a "Stay out" sign pops up and the person and dog step back.
   Vanilla JS + inline SVG, no network. Mount: <div data-anim="bloom"></div>
   Optional data-anim-mode="end" shows the finished picture with no Play button. */
(function () {
	"use strict";
	var P = "a-bloom-";
	var NS = "http://www.w3.org/2000/svg";
	var END = 9.4; // seconds

	/* Timeline (seconds). */
	var T = {
		chip1: 0.1, seedPulse: 0.2, grow: 1.2, growSpan: 2.6, tint: 1.5, tintSpan: 2.8,
		bloom: 4.2, chip2: 5.2, warns: [5.5, 6.0, 6.5], chip3: 7.1, sign: 7.3, walk: 7.9, walkSpan: 0.9
	};

	var CSS = [
		"." + P + "root{width:100%;max-width:1000px;margin:0 auto;}",
		"." + P + "root svg." + P + "svg{display:block;width:100%;height:auto;max-height:calc(50vh - 20px);max-height:calc(50dvh - 20px);margin:0 auto;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;}",
		"@media (max-height:820px) and (min-width:861px){." + P + "root svg." + P + "svg{max-height:calc(46vh - 16px);max-height:calc(46dvh - 16px);}}",
		"." + P + "bar{display:flex;justify-content:center;margin:8px 0 0;}",
		"." + P + "btn{font:inherit;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;font-weight:800;font-size:clamp(16px,1.6vw,22px);line-height:1;border:0;border-radius:999px;padding:10px 26px;background:#073e77;color:#fff;cursor:pointer;box-shadow:0 3px 0 rgba(11,18,32,.25);}",
		"." + P + "btn:hover{background:#0a4f97;}",
		"." + P + "btn:focus-visible{outline:4px solid #fece00;outline-offset:3px;}",
		"." + P + "btn:active{transform:translateY(2px);box-shadow:none;}",
		"." + P + "narrow ." + P + "two{display:none;}",
		"." + P + "root:not(." + P + "narrow) ." + P + "one{display:none;}"
	].join("\n");

	/* Shapes copied from the symbols at the top of bioglow-judging.html (viewBox 0 0 64 64). */
	var ALGAE = [[14, 20, 6], [30, 14, 5], [46, 22, 7], [22, 36, 7], [40, 40, 6], [54, 44, 5], [12, 50, 5], [28, 54, 6], [46, 56, 4]];
	var PERSON = '<circle cx="32" cy="13" r="9"/><path d="M18 60V36c0-8 6-13 14-13s14 5 14 13v24h-8V40h-2v20H28V40h-2v20z"/>';
	var DOG = '<path d="M14 30c-4-1-7-5-7-9 3 3 6 4 9 4h22l4-8c1-3 4-4 7-4h3l3 4 4 1v4c0 3-2 5-5 5h-3l-1 6v24h-6V44H20v13h-6V30z"/><path d="M48 13l3-6 2 7z"/><circle cx="51" cy="19" r="1.6" fill="#fff"/>';
	/* Warning triangle, re-centred on 0,0 (it was 3..61 x 5..57 in the 64 box). */
	var WARN = '<g transform="translate(-32,-33)"><path d="M32 5l29 52H3z" fill="#fece00" stroke="#0b1220" stroke-width="4" stroke-linejoin="round"/><rect x="29" y="22" width="6" height="20" rx="2" fill="#0b1220"/><circle cx="32" cy="49" r="3.5" fill="#0b1220"/></g>';

	/* The lake (an ellipse-ish blob) and where things sit. */
	var LAKE = "M22 140C18 66 140 12 330 14C520 10 676 52 670 136C664 214 556 266 352 262C160 266 26 220 22 140Z";
	var LC = { x: 346, y: 138, rx: 326, ry: 124 };
	var SEEDS = [[150, 112], [318, 58], [560, 140], [425, 205], [232, 196]];
	var CLUSTERS = [[130, 120], [245, 62], [380, 52], [510, 78], [600, 150], [500, 205], [360, 212], [220, 198], [105, 178]];
	var WARNED = [0, 3, 6]; // only SOME clusters make poison
	var GROUND = 254;
	var CHIP_TEXT = [["Algae grow", "too much"], ["Some make", "poison"], ["People and dogs", "can get sick"]];

	function inLake(x, y, k) {
		var dx = (x - LC.x) / (LC.rx * k), dy = (y - LC.y) / (LC.ry * k);
		return dx * dx + dy * dy <= 1;
	}
	function rng(seed) { // mulberry32, so the picture is the same every time
		return function () {
			seed |= 0; seed = seed + 0x6D2B79F5 | 0;
			var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
			t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
			return ((t ^ t >>> 14) >>> 0) / 4294967296;
		};
	}
	function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
	function prog(t, start, dur) { return clamp01((t - start) / dur); }
	function easeOut(x) { return 1 - Math.pow(1 - x, 3); }
	function easeInOut(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
	function pop(x) { // overshoot a little, then settle
		if (x <= 0) return 0; if (x >= 1) return 1;
		var c1 = 1.70158, c3 = c1 + 1;
		return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
	}
	function mk(tag, attrs, parent) {
		var n = document.createElementNS(NS, tag);
		for (var k in attrs) if (attrs.hasOwnProperty(k)) n.setAttribute(k, attrs[k]);
		if (parent) parent.appendChild(n);
		return n;
	}

	function injectCss() {
		if (document.getElementById("anim-bloom-css")) return;
		var s = document.createElement("style");
		s.id = "anim-bloom-css";
		s.textContent = CSS;
		(document.head || document.documentElement).appendChild(s);
	}

	/* All the algae dots: 5 seeds, then cluster dots and loose dots that "split off" a nearby dot. */
	function makeDots() {
		var r = rng(65773), dots = [], i, j;
		SEEDS.forEach(function (s) { dots.push({ x: s[0], y: s[1], r: 9.5, at: 0, seed: true }); });
		CLUSTERS.forEach(function (c, ci) {
			var a = r() * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a), S = 1.35;
			ALGAE.forEach(function (d) {
				var ox = (d[0] - 32.5) * S, oy = (d[1] - 34) * S;
				var x = c[0] + ox * ca - oy * sa, y = c[1] + ox * sa + oy * ca;
				if (inLake(x, y, 0.95)) dots.push({ x: x, y: y, r: d[2] * S, cl: ci });
			});
		});
		for (i = 0; i < 110; i++) {
			var x = LC.x + (r() * 2 - 1) * LC.rx, y = LC.y + (r() * 2 - 1) * LC.ry;
			if (!inLake(x, y, 0.9)) { i--; continue; }
			dots.push({ x: x, y: y, r: 3.5 + r() * 3.5 });
		}
		/* When each dot appears: the further from a seed, the later (a spreading wave that speeds up). */
		var maxD = 0;
		dots.forEach(function (d) {
			if (d.seed) return;
			d.dist = Infinity;
			SEEDS.forEach(function (s) { d.dist = Math.min(d.dist, Math.hypot(d.x - s[0], d.y - s[1])); });
			maxD = Math.max(maxD, d.dist);
		});
		dots.forEach(function (d) {
			if (d.seed) return;
			d.at = T.grow + T.growSpan * Math.pow(d.dist / maxD, 0.75) + r() * 0.25;
		});
		dots.sort(function (a, b) { return a.at - b.at; });
		/* Each new dot grows out of the nearest dot that is already there. */
		for (i = 0; i < dots.length; i++) {
			var d = dots[i];
			if (d.seed) continue;
			var best = null, bd = Infinity;
			for (j = 0; j < i; j++) {
				if (dots[j].at > d.at - 0.12) continue;
				var dd = Math.hypot(dots[j].x - d.x, dots[j].y - d.y);
				if (dd < bd) { bd = dd; best = dots[j]; }
			}
			d.px = best ? best.x : d.x; d.py = best ? best.y : d.y;
		}
		return dots;
	}

	function build(root, mode) {
		root.innerHTML = "";
		root.classList.add(P + "root");

		var svg = mk("svg", {
			"class": P + "svg", viewBox: "0 0 1000 380", role: "img",
			"aria-label": "A lake with a few blue-green algae. The algae grow too much and the water turns green: a bloom. Some of the algae make poison. A Stay out sign goes up, and a person and a dog stay away, because people and dogs can get sick."
		}, null);
		root.appendChild(svg);

		var defs = mk("defs", {}, svg);
		var clip = mk("clipPath", { id: P + "clip-" + (++uid) }, defs);
		mk("path", { d: LAKE }, clip);

		/* Land and lake */
		mk("rect", { x: 0, y: 0, width: 1000, height: 272, rx: 22, fill: "#efe4c8" }, svg);
		mk("path", { d: LAKE, fill: "#cfe8f3" }, svg);
		var waves = mk("g", { fill: "none", stroke: "#7fb3cf", "stroke-width": 5, "stroke-linecap": "round" }, svg);
		mk("path", { d: "M175 236q15-10 30 0t30 0t30 0" }, waves);
		mk("path", { d: "M420 38q15-10 30 0t30 0t30 0" }, waves);
		mk("path", { d: "M70 150q15-10 30 0t30 0" }, waves);
		var tint = mk("path", { d: LAKE, fill: "#6aa832", opacity: 0 }, svg);

		var dotsG = mk("g", { fill: "#2a9d8f", "clip-path": "url(#" + clip.id + ")" }, svg);
		var dots = makeDots();
		dots.forEach(function (d) { d.n = mk("circle", { cx: d.x, cy: d.y, r: d.seed ? d.r : 0 }, dotsG); });
		mk("path", { d: LAKE, fill: "none", stroke: "#7fb3cf", "stroke-width": 5 }, svg);

		/* "Bloom!" label */
		var bloom = mk("g", { opacity: 0 }, svg);
		mk("rect", { x: -112, y: -38, width: 224, height: 76, rx: 38, fill: "#fff", stroke: "#2a9d8f", "stroke-width": 6 }, bloom);
		var bt = mk("text", { x: 0, y: 17, "text-anchor": "middle", "font-size": 50, "font-weight": 800, fill: "#1d6f66" }, bloom);
		bt.textContent = "Bloom!";

		/* Warning marks on SOME clusters */
		var warns = WARNED.map(function (ci) {
			var g = mk("g", { opacity: 0 }, svg);
			g.innerHTML = WARN;
			return { n: g, x: CLUSTERS[ci][0], y: CLUSTERS[ci][1] };
		});

		/* Stay out sign on the shore */
		var sign = mk("g", { opacity: 0 }, svg);
		mk("rect", { x: 632, y: 100, width: 14, height: GROUND - 100, rx: 3, fill: "#8d6e4f" }, sign);
		mk("rect", { x: 546, y: 30, width: 236, height: 82, rx: 14, fill: "#fff", stroke: "#d7263d", "stroke-width": 6 }, sign);
		var sw = mk("g", { transform: "translate(584,72) scale(0.8)" }, sign);
		sw.innerHTML = WARN;
		var st = mk("text", { x: 694, y: 83, "text-anchor": "middle", "font-size": 32, "font-weight": 800, fill: "#d7263d" }, sign);
		st.textContent = "Stay out";

		/* Person and dog on the shore */
		var walkers = mk("g", {}, svg);
		var dog = mk("g", { transform: "translate(699.75," + (GROUND - 57 * 1.5) + ") scale(1.5)", fill: "#8d6e4f" }, walkers);
		dog.innerHTML = DOG;
		var person = mk("g", { transform: "translate(797.6," + (GROUND - 60 * 1.95) + ") scale(1.95)", fill: "#073e77" }, walkers);
		person.innerHTML = PERSON;

		/* The three steps (the slide's old captions) */
		var chips = CHIP_TEXT.map(function (lines, k) {
			var g = mk("g", {}, svg);
			var rect = mk("rect", { rx: 18, fill: "#fff", stroke: "#073e77", "stroke-width": 4 }, g);
			var badge = mk("circle", { fill: "#fece00", stroke: "#0b1220", "stroke-width": 3 }, g);
			var num = mk("text", { "text-anchor": "middle", "font-weight": 800, fill: "#0b1220" }, g);
			num.textContent = String(k + 1);
			var two = mk("text", { "class": P + "two", "text-anchor": "middle", "font-size": 30, "font-weight": 700, fill: "#0b1220" }, g);
			two.innerHTML = '<tspan dy="0">' + lines[0] + '</tspan><tspan dy="34">' + lines[1] + "</tspan>";
			var one = mk("text", { "class": P + "one", "text-anchor": "middle", "font-size": 54, "font-weight": 700, fill: "#0b1220" }, g);
			one.textContent = lines.join(" ");
			return { g: g, rect: rect, badge: badge, num: num, two: two, one: one, at: [T.chip1, T.chip2, T.chip3][k] };
		});

		function layout(narrow) {
			root.classList.toggle(P + "narrow", narrow);
			svg.setAttribute("viewBox", narrow ? "0 0 1000 666" : "0 0 1000 380");
			chips.forEach(function (c, k) {
				var x, y, w, h;
				if (narrow) { x = 10; y = 284 + k * 128; w = 980; h = 116; }
				else { x = 10 + k * 330; y = 284; w = 320; h = 92; }
				c.box = { x: x, y: y, w: w, h: h };
				c.rect.setAttribute("x", x); c.rect.setAttribute("y", y);
				c.rect.setAttribute("width", w); c.rect.setAttribute("height", h);
				var br = narrow ? 34 : 19, bx = x + (narrow ? 62 : 32), by = y + h / 2;
				c.badge.setAttribute("cx", bx); c.badge.setAttribute("cy", by); c.badge.setAttribute("r", br);
				c.num.setAttribute("x", bx); c.num.setAttribute("y", by + (narrow ? 14 : 9));
				c.num.setAttribute("font-size", narrow ? 40 : 26);
				var tx = narrow ? x + w / 2 + 40 : x + 32 + br + (w - 32 - br) / 2;
				c.two.setAttribute("x", tx); c.two.setAttribute("y", y + 40);
				Array.prototype.forEach.call(c.two.childNodes, function (ts) { ts.setAttribute("x", tx); });
				c.one.setAttribute("x", tx); c.one.setAttribute("y", y + h / 2 + 19);
			});
		}

		/* Draw the picture as it looks at time t (0 = start, END = finished). */
		function render(t) {
			var i, p;
			for (i = 0; i < dots.length; i++) {
				var d = dots[i];
				if (d.seed) {
					p = prog(t, T.seedPulse, 1.0);
					d.n.setAttribute("r", (d.r * (1 + 0.45 * Math.sin(Math.PI * p))).toFixed(2));
					continue;
				}
				p = prog(t, d.at, 0.45);
				if (p <= 0) { d.n.setAttribute("r", 0); continue; }
				var e = easeOut(p);
				d.n.setAttribute("cx", (d.px + (d.x - d.px) * e).toFixed(1));
				d.n.setAttribute("cy", (d.py + (d.y - d.py) * e).toFixed(1));
				d.n.setAttribute("r", (d.r * pop(p)).toFixed(2));
			}
			tint.setAttribute("opacity", (0.6 * easeInOut(prog(t, T.tint, T.tintSpan))).toFixed(3));
			waves.setAttribute("opacity", (1 - prog(t, T.tint, 1.6)).toFixed(3));

			p = pop(prog(t, T.bloom, 0.5));
			bloom.setAttribute("opacity", p > 0 ? 1 : 0);
			bloom.setAttribute("transform", "translate(" + LC.x + "," + LC.y + ") scale(" + p.toFixed(3) + ")");

			warns.forEach(function (w, k) {
				var s = pop(prog(t, T.warns[k], 0.45));
				w.n.setAttribute("opacity", s > 0 ? 1 : 0);
				w.n.setAttribute("transform", "translate(" + w.x + "," + w.y + ") scale(" + (0.95 * s).toFixed(3) + ")");
			});

			p = pop(prog(t, T.sign, 0.5));
			sign.setAttribute("opacity", p > 0 ? 1 : 0);
			sign.setAttribute("transform", "translate(639," + GROUND + ") scale(" + p.toFixed(3) + ") translate(-639,-" + GROUND + ")");

			p = prog(t, T.walk, T.walkSpan);
			var dx = 100 * easeInOut(p), bob = p > 0 && p < 1 ? -6 * Math.abs(Math.sin(p * Math.PI * 4)) : 0;
			walkers.setAttribute("transform", "translate(" + dx.toFixed(1) + "," + bob.toFixed(1) + ")");

			chips.forEach(function (c) {
				var a = easeOut(prog(t, c.at, 0.4)), b = c.box;
				var s = 1 + 0.07 * Math.sin(Math.PI * a), cx = b.x + b.w / 2, cy = b.y + b.h / 2;
				c.g.setAttribute("opacity", (0.42 + 0.58 * a).toFixed(3));
				c.g.setAttribute("transform", "translate(" + cx + "," + cy + ") scale(" + s.toFixed(3) + ") translate(" + -cx + "," + -cy + ")");
				c.rect.setAttribute("stroke", a > 0.5 ? "#073e77" : "#c9d6e3");
				c.badge.setAttribute("fill", a > 0.5 ? "#fece00" : "#e5e7eb");
			});
		}

		/* Narrow screens (phones) stack the steps so their words stay readable. */
		var narrowNow = null;
		function checkWidth() {
			var n = root.clientWidth > 0 && root.clientWidth < 560;
			if (n !== narrowNow) { narrowNow = n; layout(n); render(cur); }
		}

		var cur = 0, raf = 0, t0 = 0, btn = null;
		var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");

		function setLabel(replay) {
			if (!btn) return;
			btn.textContent = replay ? "↻ Replay" : "▶︎ Play";
			btn.setAttribute("aria-label", replay ? "Replay the bloom animation" : "Play the bloom animation");
		}
		function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
		function reset() { stop(); cur = 0; render(0); setLabel(false); }
		function tick(now) {
			cur = Math.min(END, (now - t0) / 1000);
			render(cur);
			if (cur >= END) { raf = 0; setLabel(true); return; }
			raf = requestAnimationFrame(tick);
		}
		function play() {
			stop();
			if (reduce && reduce.matches) { cur = END; render(END); setLabel(true); return; }
			cur = 0; render(0); setLabel(false);
			t0 = performance.now();
			raf = requestAnimationFrame(tick);
		}

		if (mode !== "end") {
			var bar = document.createElement("div");
			bar.className = P + "bar";
			btn = document.createElement("button");
			btn.type = "button";
			btn.className = P + "btn";
			setLabel(false);
			btn.addEventListener("click", function (e) { e.stopPropagation(); play(); btn.blur(); });
			/* Keep Enter / Space on the button from also moving the slide deck. */
			btn.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") e.stopPropagation(); });
			bar.appendChild(btn);
			root.appendChild(bar);
		}

		checkWidth();
		if (window.ResizeObserver) new ResizeObserver(checkWidth).observe(root);
		else window.addEventListener("resize", checkWidth);

		if (mode === "end") { cur = END; render(END); }
		else render(0);

		/* Back to the start whenever the slide is left. */
		var slide = root.closest ? root.closest(".slide") : null;
		if (slide && mode !== "end" && window.MutationObserver) {
			new MutationObserver(function () {
				if (!slide.classList.contains("active")) reset();
			}).observe(slide, { attributes: true, attributeFilter: ["class"] });
		}

		return { play: play, reset: reset, render: render, end: END };
	}

	var uid = 0;
	function mount(el) {
		if (!el || el.__afBloom) return el && el.__afBloom;
		injectCss();
		el.__afBloom = build(el, el.getAttribute("data-anim-mode") || "");
		return el.__afBloom;
	}

	window.AF1Anim = window.AF1Anim || {};
	window.AF1Anim["bloom"] = { mount: mount };

	function mountAll() {
		Array.prototype.forEach.call(document.querySelectorAll('[data-anim="bloom"]'), mount);
	}
	if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountAll);
	else mountAll();
})();
