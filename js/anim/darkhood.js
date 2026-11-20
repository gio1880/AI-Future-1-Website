/* "darkhood" animation: the dark hood with zigzag water paths.
   Water gets in through the zigzags; straight sunlight hits the wall.
   Optional mini-scene "Without hood": sunlight floods the sensor, messy reading.
   Vanilla JS + inline SVG. Mount with <div data-anim="darkhood"></div>.
   data-anim-mode="simple" hides the "Without hood" button. */
(function () {
	"use strict";
	var N = "darkhood", P = "a-darkhood-";
	var SVGNS = "http://www.w3.org/2000/svg";
	var uid = 0;

	var CSS = [
		"." + P + "wrap{ width:100%; max-width:1000px; margin:0 auto; font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial; }",
		"." + P + "wrap svg{ display:block; width:100%; height:auto; max-height:50vh; max-height:50dvh; margin:0 auto; }",
		"." + P + "bar{ display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:8px 16px; margin-top:8px; }",
		"." + P + "cap{ flex:0 1 560px; min-height:1.3em; font-size:clamp(20px,2.6vw,34px); font-weight:800; line-height:1.2; color:#073e77; text-align:center; }",
		"." + P + "cap ." + P + "c2{ color:#0b1220; }",
		"." + P + "btn{ font:inherit; font-size:clamp(16px,1.6vw,21px); font-weight:800; border:0; border-radius:12px; padding:10px 20px; background:#073e77; color:#fff; cursor:pointer; min-width:7.5em; }",
		"." + P + "btn:hover{ background:#0a5099; }",
		"." + P + "btn:focus-visible{ outline:4px solid #fece00; outline-offset:2px; }",
		"." + P + "btn." + P + "ghost{ background:#fff; color:#073e77; border:2px solid rgba(7,62,119,.35); min-width:0; }",
		"." + P + "btn." + P + "ghost:hover{ background:#eaf1f8; }",
		"@media (max-height:820px) and (min-width:861px){ ." + P + "wrap svg{ max-height:46vh; max-height:46dvh; } ." + P + "bar{ margin-top:4px; } ." + P + "btn{ padding:8px 18px; } }"
	].join("\n");

	function injectCSS() {
		if (document.getElementById("anim-" + N + "-css")) return;
		var s = document.createElement("style");
		s.id = "anim-" + N + "-css";
		s.textContent = CSS;
		(document.head || document.documentElement).appendChild(s);
	}

	/* ---------- helpers ---------- */
	function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
	function ease(x) { x = clamp01(x); return x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2; }
	function prog(t, a, b) { return ease((t - a) / (b - a)); }
	function lin(t, a, b) { return clamp01((t - a) / (b - a)); }
	function pop(t, a) { /* 0 -> 1.15 -> 1 over 0.35 s */
		var x = clamp01((t - a) / .35);
		if (x <= 0) return 0;
		return x < .6 ? (x / .6) * 1.15 : 1.15 - (x - .6) / .4 * .15;
	}
	function polyLen(pts) { var L = 0; for (var i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }
	function polyAt(pts, f) {
		var L = polyLen(pts) * clamp01(f);
		for (var i = 1; i < pts.length; i++) {
			var a = pts[i - 1], b = pts[i], d = Math.hypot(b[0] - a[0], b[1] - a[1]);
			if (L <= d || i === pts.length - 1) { var k = d ? Math.min(1, L / d) : 0; return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k]; }
			L -= d;
		}
		return pts[pts.length - 1];
	}

	/* ---------- the drawing ---------- */
	/* Layout (viewBox 1000 x 500), top view cut in half, like our 3D model picture:
	   sensor body on the left (sensor + tube), clear window at x 440-458,
	   dark hood on the right: two layers of walls at the top and at the bottom,
	   with the openings offset so the path zigzags. Sun at the top right. */
	var DARK = "#2f343a";
	var WATER = "#9fd0e8";
	var EMPTY = "#ffffff";
	var SUN = [900, 50];
	/* Rays (main scene): all stop on a wall. The middle one goes into the zigzag. */
	var RAYS = [[650, 90], [705, 145]];
	/* Rays (no hood): straight onto the window. */
	var RAYS2 = [[458, 190], [458, 250], [458, 310]];
	/* Algae dots that travel in with the water: start in the lake, end at the checked spot. */
	var TOPR = [[790, 128], [570, 128], [570, 205]];
	var BOTR = [[790, 372], [570, 372], [570, 295]];
	var DOTS = [
		{ s: [770, 18], r: TOPR, e: [522, 232], t0: .3, c: "#2a9d8f", rad: 9 },
		{ s: [812, 52], r: TOPR, e: [548, 244], t0: .95, c: "#6aa832", rad: 8 },
		{ s: [796, 34], r: TOPR, e: [512, 252], t0: 1.6, c: "#2a9d8f", rad: 8 },
		{ s: [808, 482], r: BOTR, e: [540, 268], t0: .55, c: "#2a9d8f", rad: 9 },
		{ s: [772, 448], r: BOTR, e: [518, 278], t0: 1.2, c: "#6aa832", rad: 8 },
		{ s: [794, 500], r: BOTR, e: [552, 258], t0: 1.85, c: "#2a9d8f", rad: 8 }
	];
	var T_MAIN = 9.0, T_NOHOOD = 6.0;
	/* rays start at the edge of the sun */
	function rayStart(e) { var dx = e[0] - SUN[0], dy = e[1] - SUN[1], d = Math.hypot(dx, dy); return [SUN[0] + dx / d * 34, SUN[1] + dy / d * 34]; }
	function rayLen(e) { var s0 = rayStart(e); return Math.hypot(e[0] - s0[0], e[1] - s0[1]); }

	function svgMarkup(id) {
		var clip = P + "clip-" + id;
		/* open space inside the hood (empty before the water comes in) */
		var open = [
			[760, 90, 60, 25], [470, 115, 410, 30], [540, 145, 60, 25],   /* top: entry gap, passage, exit gap */
			[458, 170, 422, 160],                                          /* chamber */
			[540, 330, 60, 25], [470, 355, 410, 30], [760, 385, 60, 25]   /* bottom */
		];
		var openRects = open.map(function (r) { return '<rect x="' + r[0] + '" y="' + r[1] + '" width="' + r[2] + '" height="' + r[3] + '"/>'; }).join("");
		var walls = [
			[440, 90, 30, 80], [440, 330, 30, 80],          /* posts next to the window */
			[470, 90, 290, 25], [820, 90, 90, 25],          /* top outer layer (gap 760-820) */
			[470, 145, 70, 25], [600, 145, 280, 25],        /* top inner layer (gap 540-600) */
			[470, 330, 70, 25], [600, 330, 280, 25],        /* bottom inner layer */
			[470, 385, 290, 25], [820, 385, 90, 25],        /* bottom outer layer */
			[880, 90, 30, 320]                              /* far wall */
		];
		var wallRects = walls.map(function (r) { return '<rect x="' + r[0] + '" y="' + r[1] + '" width="' + r[2] + '" height="' + r[3] + '" rx="3"/>'; }).join("");
		var lakeDots = [[60, 30, 7], [150, 60, 6], [250, 22, 7], [330, 70, 6], [960, 140, 7], [945, 250, 6], [968, 360, 7], [60, 470, 7], [190, 440, 6], [330, 480, 7], [700, 30, 6], [640, 470, 6], [930, 470, 7], [600, 20, 7]]
			.map(function (d, i) { return '<circle cx="' + d[0] + '" cy="' + d[1] + '" r="' + d[2] + '" fill="' + (i % 3 ? "#2a9d8f" : "#6aa832") + '" opacity=".75"/>'; }).join("");
		var sunRays = "";
		for (var k = 0; k < 12; k++) {
			var a = k * Math.PI / 6, c = Math.cos(a), s = Math.sin(a);
			sunRays += '<line x1="' + (SUN[0] + c * 36).toFixed(1) + '" y1="' + (SUN[1] + s * 36).toFixed(1) + '" x2="' + (SUN[0] + c * 47).toFixed(1) + '" y2="' + (SUN[1] + s * 47).toFixed(1) + '"/>';
		}
		function rayLines(list, cls) {
			return list.map(function (e, i) { var s0 = rayStart(e); return '<line class="' + P + cls + '" data-i="' + i + '" x1="' + s0[0].toFixed(1) + '" y1="' + s0[1].toFixed(1) + '" x2="' + e[0] + '" y2="' + e[1] + '"/>'; }).join("");
		}
		function blockMark(e, i) {
			return '<g class="' + P + 'block" data-i="' + i + '" transform="translate(' + e[0] + ' ' + e[1] + ')"><g class="' + P + 's">' +
				'<path d="M-24 -6l-10 -6M-22 8l-12 4M-10 -20l-4 -10" stroke="#fece00" stroke-width="5" stroke-linecap="round"/>' +
				'<circle r="15" fill="#d7263d" stroke="#fff" stroke-width="3"/>' +
				'<path d="M-6 -6l12 12M6 -6l-12 12" stroke="#fff" stroke-width="4.5" stroke-linecap="round"/></g></g>';
		}
		return '' +
			'<svg viewBox="0 0 1000 500" xmlns="' + SVGNS + '" role="img" aria-labelledby="' + P + 'title-' + id + '">' +
			'<title id="' + P + 'title-' + id + '">Top view of the dark hood cut in half. Water comes in through zigzag paths and reaches the window in front of the sensor. Sunlight travels straight, hits the walls and stops, so the sensor stays dark.</title>' +
			'<defs><clipPath id="' + clip + '">' + openRects + '</clipPath>' +
			'<radialGradient id="' + P + 'glow-' + id + '"><stop offset="0" stop-color="#fece00" stop-opacity=".95"/><stop offset=".6" stop-color="#fece00" stop-opacity=".45"/><stop offset="1" stop-color="#fece00" stop-opacity="0"/></radialGradient></defs>' +
			/* lake */
			'<rect x="0" y="0" width="1000" height="500" rx="22" fill="' + WATER + '"/>' +
			'<g>' + lakeDots + '</g>' +
			/* inside of the hood: empty at first */
			'<g class="' + P + 'empty" fill="' + EMPTY + '">' + openRects + '</g>' +
			/* water coming in (clipped to the open space) */
			'<g clip-path="url(#' + clip + ')">' +
			'<path class="' + P + 'wtop" d="M790 60V130H570V230" fill="none" stroke="' + WATER + '" stroke-width="84" stroke-linejoin="round"/>' +
			'<path class="' + P + 'wbot" d="M790 440V370H570V270" fill="none" stroke="' + WATER + '" stroke-width="84" stroke-linejoin="round"/>' +
			'<g class="' + P + 'wall" fill="' + WATER + '">' + openRects + '</g>' +
			'<rect class="' + P + 'ctop" x="458" y="170" width="422" height="0" fill="' + WATER + '"/>' +
			'<rect class="' + P + 'cbot" x="458" y="330" width="422" height="0" fill="' + WATER + '"/>' +
			'</g>' +
			/* the spot where the water is checked */
			'<circle cx="532" cy="255" r="40" fill="none" stroke="#073e77" stroke-width="3" stroke-dasharray="8 7" opacity=".7"/>' +
			/* no-hood light wash (hidden in the main scene) */
			'<g class="' + P + 'wash" opacity="0">' +
			'<polygon points="' + SUN[0] + ',' + SUN[1] + ' 458,170 458,330" fill="#fece00" opacity=".35"/>' +
			'</g>' +
			/* sensor body + tube + sensor */
			'<rect x="30" y="150" width="410" height="200" rx="8" fill="' + DARK + '"/>' +
			'<rect x="54" y="168" width="46" height="164" rx="4" fill="#fff"/>' +
			'<rect x="100" y="230" width="340" height="40" fill="#fff"/>' +
			'<rect class="' + P + 'tube" x="100" y="230" width="340" height="40" fill="#fece00" opacity="0"/>' +
			'<rect class="' + P + 'sensorglow" x="40" y="150" width="76" height="200" rx="10" fill="url(#' + P + 'glow-' + id + ')" opacity="0"/>' +
			'<rect x="66" y="178" width="18" height="144" rx="3" fill="#3a6fb0"/>' +
			/* window */
			'<rect class="' + P + 'win" x="440" y="170" width="18" height="160" fill="#bfe2ff" stroke="#1e90ff" stroke-width="3"/>' +
			/* dark hood */
			'<g class="' + P + 'hood" fill="' + DARK + '">' + wallRects + '</g>' +
			/* algae dots that swim in */
			'<g class="' + P + 'dots"></g>' +
			/* sun rays */
			'<g stroke="#f5b800" stroke-width="9" stroke-linecap="round">' + rayLines(RAYS, "ray") + rayLines(RAYS2, "ray2") + '</g>' +
			/* sun */
			'<g class="' + P + 'sun"><g stroke="#e0a800" stroke-width="6" stroke-linecap="round">' + sunRays + '</g>' +
			'<circle cx="' + SUN[0] + '" cy="' + SUN[1] + '" r="30" fill="#fece00" stroke="#e0a800" stroke-width="4"/></g>' +
			RAYS.map(blockMark).join("") +
			/* labels */
			'<g class="svgtext" font-family="system-ui,-apple-system,Segoe UI,Roboto,Arial" font-weight="800" font-size="32" fill="#0b1220">' +
			'<g stroke="#073e77" stroke-width="4" fill="none"><path d="M75 300V420"/><path d="M449 330V420"/><path class="' + P + 'hoodlead" d="M680 410V420"/></g>' +
			'<g fill="#073e77"><circle cx="75" cy="300" r="6"/><circle cx="449" cy="330" r="6"/></g>' +
			'<text x="40" y="455">Sensor</text>' +
			'<text x="449" y="455" text-anchor="middle">Window</text>' +
			'<text class="' + P + 'hoodlbl" x="680" y="455" text-anchor="middle">Dark hood</text>' +
			'</g>' +
			/* sensor badge: green check (main) / red X (no hood) */
			'<g class="' + P + 'ok" transform="translate(140 112)"><g class="' + P + 's">' +
			'<circle r="26" fill="#2e9e44" stroke="#fff" stroke-width="4"/><path d="M-12 1l8 9 16 -18" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g></g>' +
			/* no-hood gauge */
			'<g class="' + P + 'gauge" opacity="0">' +
			'<path d="M140 130 A70 70 0 0 1 280 130" fill="#fff" stroke="#0b1220" stroke-width="5"/>' +
			'<path d="M140 130 H280" stroke="#0b1220" stroke-width="5"/>' +
			'<g class="' + P + 'needle"><path d="M210 130 L210 72" stroke="#d7263d" stroke-width="7" stroke-linecap="round"/></g>' +
			'<circle cx="210" cy="130" r="8" fill="#0b1220"/>' +
			'<path d="M182 40l-8 -12M210 34v-14M238 40l8 -12" stroke="#d7263d" stroke-width="5" stroke-linecap="round" class="' + P + 'jig"/>' +
			'<text x="298" y="100" font-family="system-ui,-apple-system,Segoe UI,Roboto,Arial" font-size="32" font-weight="800" fill="#d7263d">Messy</text>' +
			'<text x="298" y="134" font-family="system-ui,-apple-system,Segoe UI,Roboto,Arial" font-size="32" font-weight="800" fill="#d7263d">reading</text>' +
			'</g>' +
			'</svg>';
	}

	function mount(el) {
		if (!el) return null;
		if (el.getAttribute("data-anim-mounted") === "1") return el.afDarkhood || null;
		el.setAttribute("data-anim-mounted", "1");
		injectCSS();
		var id = ++uid;
		var simple = (el.getAttribute("data-anim-mode") || "") === "simple";
		var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

		var wrap = document.createElement("div");
		wrap.className = P + "wrap";
		wrap.innerHTML = svgMarkup(id) +
			'<div class="' + P + 'bar">' +
			'<button type="button" class="' + P + 'btn ' + P + 'play">▶ Play</button>' +
			'<div class="' + P + 'cap" aria-live="polite"><span class="' + P + 'c1"></span> <span class="' + P + 'c2"></span></div>' +
			(simple ? "" : '<button type="button" class="' + P + 'btn ' + P + 'ghost ' + P + 'nohood">Without hood</button>') +
			'</div>';
		el.innerHTML = "";
		el.appendChild(wrap);

		function q(s) { return wrap.querySelector("." + P + s); }
		function qa(s) { return Array.prototype.slice.call(wrap.querySelectorAll("." + P + s)); }
		var empty = q("empty");
		var wtop = q("wtop"), wbot = q("wbot"), wall = q("wall"), ctop = q("ctop"), cbot = q("cbot");
		var hood = q("hood"), hoodlbl = q("hoodlbl"), hoodlead = q("hoodlead");
		var rays = qa("ray"), rays2 = qa("ray2"), blocks = qa("block");
		var ok = q("ok"), gauge = q("gauge"), needle = q("needle"), jig = q("jig");
		var wash = q("wash"), tube = q("tube"), sglow = q("sensorglow"), win = q("win");
		var c1 = q("c1"), c2 = q("c2");
		var playBtn = q("play"), noBtn = q("nohood");
		var dotG = q("dots");

		/* dots */
		var dots = DOTS.map(function (d) {
			var c = document.createElementNS(SVGNS, "circle");
			c.setAttribute("r", d.rad); c.setAttribute("fill", d.c); c.setAttribute("stroke", "#fff"); c.setAttribute("stroke-width", "2");
			dotG.appendChild(c);
			return { el: c, pts: [d.s].concat(d.r).concat([d.e]), t0: d.t0 };
		});
		var DOT_DUR = 3.4;

		/* stroke lengths for the "draw" effect */
		var LT = 70 + 220 + 100, LB = LT;
		[wtop, wbot].forEach(function (p) { p.setAttribute("stroke-dasharray", LT + " " + LT); });
		rays.forEach(function (r, i) { var L = rayLen(RAYS[i]); r.setAttribute("stroke-dasharray", L + " " + (L + 40)); });
		rays2.forEach(function (r, i) { var L = rayLen(RAYS2[i]); r.setAttribute("stroke-dasharray", L + " " + (L + 40)); });

		function setText(n, s) { if (n.textContent !== s) n.textContent = s; }
		function scaleG(g, k) {
			var inner = g.firstChild;
			inner.setAttribute("transform", "scale(" + k.toFixed(3) + ")");
			g.setAttribute("opacity", k > 0 ? 1 : 0);
		}

		/* ----- one function draws any moment of either scene ----- */
		function render(scene, t) {
			var nh = scene === "nohood";
			if (nh) t = T_MAIN; /* the water part is finished in the no-hood scene */
			var tn = nh ? arguments[2] : 0;

			/* water */
			var w = prog(t, .3, 3.2);
			wtop.setAttribute("stroke-dashoffset", (LT * (1 - w)).toFixed(1));
			wbot.setAttribute("stroke-dashoffset", (LB * (1 - w)).toFixed(1));
			var wf = prog(t, 2.6, 3.6);
			wall.setAttribute("opacity", wf.toFixed(3));
			/* once the water is full, hide the white layer under it (no hairline seams) */
			empty.setAttribute("opacity", nh || t >= 4.6 ? 0 : 1);
			var f = prog(t, 2.9, 4.5) * 80;
			ctop.setAttribute("height", f.toFixed(1));
			cbot.setAttribute("y", (330 - f).toFixed(1)); cbot.setAttribute("height", f.toFixed(1));
			dots.forEach(function (d) {
				var p = polyAt(d.pts, ease((t - d.t0) / DOT_DUR));
				d.el.setAttribute("cx", p[0].toFixed(1)); d.el.setAttribute("cy", p[1].toFixed(1));
			});

			/* main-scene sunlight */
			rays.forEach(function (r, i) {
				var L = rayLen(RAYS[i]), a = 5.0 + i * .2, k = nh ? 0 : prog(t, a, a + 1.2);
				r.setAttribute("stroke-dashoffset", (L * (1 - k)).toFixed(1));
				r.setAttribute("opacity", k > 0 ? 1 : 0);
			});
			blocks.forEach(function (b, i) { scaleG(b, nh ? 0 : pop(t, 6.2 + i * .2)); });
			scaleG(ok, nh ? 0 : pop(t, 7.2));

			/* hood (fades away in the no-hood scene) */
			var hoodOp = nh ? 1 - prog(tn, .1, .9) : 1;
			hood.setAttribute("opacity", hoodOp.toFixed(3));
			hoodlbl.setAttribute("opacity", hoodOp.toFixed(3));
			hoodlead.setAttribute("opacity", hoodOp.toFixed(3));

			/* no-hood light */
			rays2.forEach(function (r, i) {
				var L = rayLen(RAYS2[i]), a = .9 + i * .15, k = nh ? prog(tn, a, a + .9) : 0;
				r.setAttribute("stroke-dashoffset", (L * (1 - k)).toFixed(1));
				r.setAttribute("opacity", k > 0 ? 1 : 0);
			});
			var lit = nh ? prog(tn, 1.8, 2.5) : 0;
			wash.setAttribute("opacity", lit.toFixed(3));
			tube.setAttribute("opacity", (lit * .85).toFixed(3));
			sglow.setAttribute("opacity", lit.toFixed(3));
			win.setAttribute("fill", lit > .5 ? "#fff3b0" : "#bfe2ff");
			var g = nh ? prog(tn, 2.3, 2.8) : 0;
			gauge.setAttribute("opacity", g.toFixed(3));
			var ang = 0;
			if (nh) {
				var j = lin(tn, 2.5, 5.6), amp = j > 0 && j < 1 ? 1 : 0;
				ang = amp ? 55 * Math.sin(tn * 9.1) * Math.cos(tn * 3.7) + 20 * Math.sin(tn * 23) : (j >= 1 ? 38 : -20);
			}
			needle.setAttribute("transform", "rotate(" + ang.toFixed(1) + " 210 130)");
			jig.setAttribute("opacity", nh && tn > 2.5 ? 1 : 0);

			/* caption */
			setText(c1, nh ? "No hood: sunlight gets in." : "Water gets in.");
			setText(c2, nh ? "" : "Sunlight stays out.");
			c1.style.opacity = nh ? prog(tn, 2.4, 2.9) : prog(t, 4.3, 4.8);
			c2.style.opacity = nh ? 0 : prog(t, 7.5, 8.0);
		}

		/* ----- playback ----- */
		var raf = 0, start = 0, scene = "main", state = "start";
		function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
		function setLabel() {
			playBtn.textContent = (scene === "main" && state === "end") ? "↻ Replay" : "▶ Play";
			if (noBtn) noBtn.textContent = (scene === "nohood" && state !== "start") ? "↻ Without hood" : "Without hood";
		}
		function draw(s, t) { if (s === "nohood") render("nohood", 0, t); else render("main", t); }
		function reset() { stop(); scene = "main"; state = "start"; draw("main", 0); setLabel(); }
		function play(s) {
			stop(); scene = s; var T = s === "nohood" ? T_NOHOOD : T_MAIN;
			if (reduce) { draw(s, T); state = "end"; setLabel(); return; }
			state = "playing"; setLabel();
			start = performance.now();
			(function tick(now) {
				var t = (now - start) / 1000;
				if (t >= T) { draw(s, T); raf = 0; state = "end"; setLabel(); return; }
				draw(s, t);
				raf = requestAnimationFrame(tick);
			})(start);
		}

		function wire(btn, fn) {
			if (!btn) return;
			btn.addEventListener("click", function (e) { e.stopPropagation(); fn(); btn.blur(); });
			btn.addEventListener("keydown", function (e) {
				if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") e.stopPropagation();
			});
		}
		wire(playBtn, function () { play("main"); });
		wire(noBtn, function () { play("nohood"); });

		reset();

		/* reset when the slide is left */
		var slide = el.closest ? el.closest(".slide") : null;
		if (slide && window.MutationObserver) {
			var wasActive = slide.classList.contains("active");
			new MutationObserver(function () {
				var on = slide.classList.contains("active");
				if (wasActive && !on) reset();
				wasActive = on;
			}).observe(slide, { attributes: true, attributeFilter: ["class"] });
		}

		/* small handle for the deck or for testing: el.afDarkhood.seek("main", 5) */
		var api = {
			play: function (s) { play(s === "nohood" ? "nohood" : "main"); },
			reset: reset,
			seek: function (s, t) { stop(); scene = s === "nohood" ? "nohood" : "main"; state = "seek"; draw(scene, t); setLabel(); },
			duration: { main: T_MAIN, nohood: T_NOHOOD }
		};
		el.afDarkhood = api;
		return api;
	}

	window.AF1Anim = window.AF1Anim || {};
	window.AF1Anim[N] = { mount: mount };

	function mountAll() {
		var els = document.querySelectorAll('[data-anim="' + N + '"]');
		for (var i = 0; i < els.length; i++) mount(els[i]);
	}
	if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountAll);
	else mountAll();
})();
