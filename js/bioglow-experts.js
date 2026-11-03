/*
  The experts who helped AI Future 1 with SpectraFloat (BIOGLOW 2026–27).
  This is the ONLY place their names are written. bioglow-judging.html and
  bioglow-innovation.html both read it.

  - To hide every person's name and show their role instead, set SHOW_NAMES to false.
  - To hide just one person, set that person's "name" to "" (their "anon" text is shown).
  - Companies and groups have no "anon" because they are not people.
*/
window.AF1_EXPERTS = {
	SHOW_NAMES: true,

	outreach: { emailed: "about 10", replied: 7, calls: 2 },

	people: {
		sarah: {
			name: "Sarah Goodrich",
			anon: "A bloom scientist at NY State DEC",
			role: "Harmful Algal Blooms Program",
			org: "NY State Department of Environmental Conservation (DEC)",
			orgUrl: "https://dec.ny.gov/environmental-protection/water/water-quality/harmful-algal-blooms",
			how: "Video call · Oct 14",
			said: "Boat and lab tests are slow and cost a lot. Small lakes bloom too. She asked us: can a buoy warn people early?"
		},
		gobler: {
			name: "Dr. Christopher Gobler",
			anon: "A Stony Brook University scientist",
			role: "Professor · science advisor to the Lake Agawam Conservancy",
			org: "Stony Brook University, School of Marine and Atmospheric Sciences",
			orgUrl: "https://www.stonybrook.edu/somas/",
			how: "Email · Oct 30",
			said: "The sound-wave buoys tried on Lake Agawam in 2021 were “largely unsuccessful.” The lake’s buoy shares its readings online."
		},
		magyar: {
			name: "Meghan Magyar",
			anon: "A member of the Lake Agawam Conservancy",
			role: "Wrote back for the Conservancy",
			org: "Lake Agawam Conservancy (they take care of the lake)",
			orgUrl: "https://lakeagawam.org/",
			how: "Email · Oct 30",
			said: "Hydrogen peroxide worked well on the lake, but only for a few days. She sent our email to their science advisor."
		},
		shining: {
			name: "Shining Wang",
			anon: "An engineering student at Columbia",
			role: "Hardware co-lead, AQUAS team",
			org: "AQUAS, a Columbia University student robotics team",
			orgUrl: "https://news.columbia.edu/node/7632",
			how: "Video call · Oct 18",
			said: "AQUAS builds a sensor buoy, a robot boat and a bloom-forecast model for NYC lakes, with NYC Parks. She looked at our 3D model: make it low and wide, and leave room for wires."
		},
		goes: {
			name: "Dr. Joaquim Goes",
			anon: "A Columbia University scientist",
			role: "Research professor",
			org: "Columbia University, Lamont-Doherty Earth Observatory",
			orgUrl: "https://lamont.columbia.edu/",
			how: "Email · Oct 8",
			said: "He studies blooms from space, and he introduced us to the AQUAS team."
		},
		sukowski: {
			name: "Carolyn Sukowski",
			anon: "A water educator at Cornell Cooperative Extension",
			role: "Natural Resource Education Specialist",
			org: "Cornell Cooperative Extension of Suffolk County",
			orgUrl: "https://ccesuffolk.org/marine/water-quality",
			how: "Email · Oct 7",
			said: "She wrote back and asked us to send our questions by email."
		}
	},

	groups: {
		lgsonic: {
			name: "LG Sonic US",
			role: "Water technology company",
			org: "LG Sonic",
			orgUrl: "https://www.lgsonic.com/",
			how: "Email · Oct 23",
			said: "Their buoys were on Lake Agawam in 2021. They said yes to a call with our team."
		},
		atlas: {
			name: "Atlas Scientific",
			role: "Water-sensor company in Queens",
			org: "Atlas Scientific, Long Island City",
			orgUrl: "https://atlas-scientific.com/",
			how: "Email · Oct 12",
			said: "They wrote back and asked us to email our sensor questions."
		}
	},

	// Card order on both pages.
	order: ["sarah", "shining", "goes", "magyar", "gobler", "lgsonic", "atlas", "sukowski"]
};

/* Helpers used by both pages. */
window.AF1_EXPERTS.get = function (id) {
	var e = this.people[id] || this.groups[id];
	if (!e) return null;
	var person = !!this.people[id];
	var shown = person && (!this.SHOW_NAMES || !e.name) ? e.anon : e.name;
	return { id: id, person: person, title: shown, role: e.role, org: e.org, orgUrl: e.orgUrl, how: e.how, said: e.said };
};

window.AF1_EXPERTS.isAnon = function (id) {
	var p = this.people[id];
	return !!p && (!this.SHOW_NAMES || !p.name);
};

/* Fills every element with data-expert-name="id" with the name (or role) to show.
   data-mid: the name sits mid-sentence, so a role starts with a small letter ("with a Stony Brook…").
   data-named-only="id": shown only while that person's name is shown (hides repeated words). */
window.AF1_EXPERTS.fillNames = function (root) {
	var self = this;
	root = root || document;
	root.querySelectorAll("[data-expert-name]").forEach(function (el) {
		var id = el.getAttribute("data-expert-name"), e = self.get(id);
		if (!e) return;
		var t = e.title;
		if (self.isAnon(id) && el.hasAttribute("data-mid")) t = t.charAt(0).toLowerCase() + t.slice(1);
		el.textContent = t;
	});
	root.querySelectorAll("[data-named-only]").forEach(function (el) {
		if (self.isAnon(el.getAttribute("data-named-only"))) el.hidden = true;
	});
};

/* Builds one expert card. */
window.AF1_EXPERTS.card = function (id) {
	var e = this.get(id);
	var div = document.createElement("article");
	div.className = "xcard" + (e.person ? "" : " group");
	var h = document.createElement("h3");
	h.textContent = e.title;
	var role = document.createElement("p");
	role.className = "xrole";
	role.textContent = e.role;
	var org = document.createElement("a");
	org.className = "xorg";
	org.href = e.orgUrl;
	org.target = "_blank";
	org.rel = "noreferrer";
	org.textContent = e.org;
	var how = document.createElement("p");
	how.className = "xhow";
	how.textContent = e.how;
	var said = document.createElement("p");
	said.className = "xsaid";
	said.textContent = e.said;
	div.append(h, role, org, how, said);
	return div;
};

window.AF1_EXPERTS.fillCards = function (container, ids) {
	var self = this;
	(ids || this.order).forEach(function (id) { container.appendChild(self.card(id)); });
};
