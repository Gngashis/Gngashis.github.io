/* MyTravelExpert — original site behaviour (no dependencies) */
(function () {
  "use strict";

  // Sticky header state
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("scrolled", window.scrollY > 40);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // Mobile menu
  var toggle = document.querySelector(".nav-toggle");
  var menu = document.getElementById("navmenu");
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
  }

  // Reveal on scroll (respects prefers-reduced-motion via CSS)
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  // Region filter on packages.html
  var chips = document.querySelectorAll(".chip[data-region]");
  var grid = document.getElementById("all-grid");
  if (chips.length && grid) {
    var empty = document.querySelector(".empty-note");
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        chips.forEach(function (c) { c.classList.remove("is-on"); });
        chip.classList.add("is-on");
        var region = chip.getAttribute("data-region");
        var shown = 0;
        grid.querySelectorAll(".journey-card").forEach(function (cardEl) {
          var match = region === "all" ||
            cardEl.getAttribute("data-region") === region;
          cardEl.hidden = !match;
          if (match) shown++;
        });
        if (empty) empty.hidden = shown > 0;
      });
    });
  }
})();
