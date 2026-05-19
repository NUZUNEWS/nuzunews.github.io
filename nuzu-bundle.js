/**
 * NUZU News — Production Bundle
 * Includes: Performance · Accessibility · Onboarding Tour · Mobile Hardening · Security
 *
 * This is a SINGLE DROP-IN FILE. No other JS/CSS files needed.
 * bot_patch.py adds one <script> tag to bot.py that loads this file.
 * That's the entire front-end install.
 *
 * Version: 3.2.0 — US nav fix (stopImmediatePropagation removed, visual feedback added,
 *                  "already at top" forced scroll, section collapse guard on nav click)
 */
(function (w, d) {
  'use strict';

  /* ═══════════════════════════════════════════════════════════════════════
     PART 1 — INJECT HARDENING CSS
     All mobile, Safari, accessibility, and low-end device CSS.
     Injected before DOMContentLoaded to avoid FOUC.
  ═══════════════════════════════════════════════════════════════════════ */
  var HARDENING_CSS = [
    /* Text size adjust — prevents Safari iOS font jump on rotation */
    'html{-webkit-text-size-adjust:100%;text-size-adjust:100%;}',

    /* Tap highlight — transparent everywhere, subtle brand color on active interactive elements */
    '*{-webkit-tap-highlight-color:transparent;}',
    'a:active,button:active,.headline:active,.nav-tab-link:active{-webkit-tap-highlight-color:rgba(30,79,216,.15);}',

    /* Momentum scroll in panels */
    '.saved-panel-list,#wr-grid,.section-columns,.top-stories-strip{-webkit-overflow-scrolling:touch;overscroll-behavior-y:contain;}',

    /* Safe-area insets (iPhone notch / Dynamic Island / home bar) */
    '.sticky-nav{padding-top:env(safe-area-inset-top,0px);}',
    '.nuzu-bottom-nav{padding-bottom:env(safe-area-inset-bottom,0px);}',
    '@media(max-width:900px){body{padding-bottom:calc(56px + env(safe-area-inset-bottom,0px));}}',
    '#nuzu-sw-toast{bottom:calc(80px + env(safe-area-inset-bottom,0px));}',

    /* Compositor promotion — sticky nav + bottom nav on own GPU layer */
    '.sticky-nav,.nuzu-bottom-nav{transform:translateZ(0);}',

    /* content-visibility intrinsic size hint (avoids collapsed sections off-screen) */
    '.section-wrap{contain-intrinsic-size:auto 800px;}',

    /* Scroll margin — sections land below sticky nav when scrolled to */
    '.section-wrap{scroll-margin-top:60px;}',
    '@media(max-width:900px){.section-wrap{scroll-margin-top:74px;}}',

    /* Touch target sizing — bookmark/share buttons to WCAG 2.5.8 minimum */
    '@media(max-width:900px){',
    '.bookmark-btn,.share-btn,.link{min-height:36px;min-width:36px;display:inline-flex;align-items:center;justify-content:center;padding:0 6px;}',
    '.headline{padding-top:8px;padding-bottom:8px;}',
    '.nav-tab-link{padding:10px 14px;min-height:44px;display:inline-flex;align-items:center;}',
    '}',

    /* LOW-END OVERRIDES (class added by performance section below) */
    'html.nz-low .sticky-nav,html.nz-low .saved-panel,html.nz-low #nuzu-tour-tip,html.nz-low #nuzu-sw-toast{backdrop-filter:none!important;-webkit-backdrop-filter:none!important;}',
    'html.nz-low .cluster{box-shadow:none!important;}',
    'html.nz-low .headline{transition:none!important;}',
    'html.nz-low .bb-pulse-dot,html.nz-low .new-dot{animation:none!important;}',

    /* SLOW-CONNECTION OVERRIDES */
    'html.nz-slow .nuzu-thumb,html.nz-slow .nuzu-thumb-md{display:none!important;}',
    'html.nz-slow *,html.nz-slow *::before,html.nz-slow *::after{transition-duration:.1s!important;}',

    /* REDUCED MOTION */
    '@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;scroll-behavior:auto!important;}}',

    /* FOCUS VISIBLE — high-contrast focus rings for keyboard nav */
    ':focus-visible{outline:3px solid #7EB3FF!important;outline-offset:3px!important;border-radius:3px;}',
    ':focus:not(:focus-visible){outline:none!important;}',

    /* SKIP LINK */
    '#nz-skip{position:fixed;top:-100px;left:12px;z-index:99999;background:#1E4FD8;color:#fff;',
    'padding:10px 18px;border-radius:0 0 8px 8px;font-family:"Inter",Arial,sans-serif;',
    'font-size:.9em;font-weight:700;text-decoration:none;transition:top .15s ease;',
    'box-shadow:0 4px 12px rgba(0,0,0,.5);}',
    '#nz-skip:focus{top:0;outline:3px solid #7EB3FF;outline-offset:2px;}',

    /* SW UPDATE TOAST */
    '#nz-toast{position:fixed;bottom:80px;left:50%;transform:translateX(-50%) translateY(20px);',
    'z-index:9998;background:#0A1628;border:1px solid #1E4FD8;border-radius:10px;',
    'padding:12px 18px;display:flex;align-items:center;gap:12px;',
    'box-shadow:0 4px 24px rgba(0,0,0,.6);font-family:"Inter",Arial,sans-serif;',
    'font-size:.84em;color:#C8D8EE;white-space:nowrap;',
    'opacity:0;transition:opacity .3s,transform .3s;pointer-events:none;}',
    '#nz-toast.on{opacity:1;transform:translateX(-50%) translateY(0);pointer-events:auto;}',
    '#nz-toast-ok{background:#1E4FD8;color:#fff;border:none;border-radius:6px;',
    'padding:6px 14px;font-size:.9em;font-weight:700;cursor:pointer;font-family:"Inter",Arial,sans-serif;}',
    '#nz-toast-x{background:none;border:none;color:#4A6A99;font-size:1.1em;cursor:pointer;padding:0 2px;}',

    /* TOUR OVERLAY */
    '@keyframes nz-in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}',
    '@keyframes nz-pulse{0%,100%{box-shadow:0 0 0 0 rgba(30,79,216,.35)}70%{box-shadow:0 0 0 10px rgba(30,79,216,0)}}',
    '#nz-tour-bd{position:fixed;inset:0;z-index:10000;pointer-events:none;}',
    '.nz-quad{position:fixed;background:rgba(2,9,18,.88);transition:all .28s cubic-bezier(.4,0,.2,1);}',
    '#nz-ring{position:fixed;z-index:10001;pointer-events:none;border-radius:6px;',
    'box-shadow:0 0 0 3px #1E4FD8,0 0 0 6px rgba(30,79,216,.25);',
    'transition:all .28s cubic-bezier(.4,0,.2,1);animation:nz-pulse 2s infinite;}',
    '#nz-tip{position:fixed;z-index:10002;background:#0A1628;border:1px solid #1E4FD8;',
    'border-radius:12px;padding:20px 22px 16px;max-width:320px;min-width:260px;',
    'box-shadow:0 8px 40px rgba(0,0,0,.7),0 0 0 1px rgba(30,79,216,.2);',
    'animation:nz-in .22s ease both;font-family:"Inter",Arial,sans-serif;}',
    '#nz-tip h3{color:#fff;font-size:1em;font-weight:700;margin:0 0 8px;line-height:1.35;}',
    '#nz-tip p{color:#A8C0E0;font-size:.85em;line-height:1.6;margin:0 0 14px;}',
    '.nz-dots{display:flex;gap:5px;margin-bottom:14px;}',
    '.nz-dot{width:6px;height:6px;border-radius:50%;background:#1A2E50;transition:background .2s;}',
    '.nz-dot.on{background:#1E4FD8;}.nz-dot.done{background:#4A8AFF;}',
    '.nz-btns{display:flex;align-items:center;gap:10px;}',
    '.nz-cta{background:#1E4FD8;color:#fff;border:none;border-radius:7px;',
    'padding:9px 18px;font-size:.84em;font-weight:700;cursor:pointer;flex:1;',
    'font-family:"Inter",Arial,sans-serif;transition:background .15s;}',
    '.nz-cta:hover{background:#2563EB;}',
    '.nz-skip{background:none;border:none;color:#4A6A99;font-size:.76em;',
    'cursor:pointer;text-decoration:underline;white-space:nowrap;font-family:"Inter",Arial,sans-serif;}',
    '.nz-skip:hover{color:#7EB3FF;}',

    /* KEYBOARD SHORTCUT POPUP */
    '#nz-keys{position:fixed;bottom:80px;right:12px;z-index:9997;background:#0A1628;',
    'border:1px solid #1E4FD8;border-radius:10px;padding:14px 18px;',
    'font-family:"Inter",Arial,sans-serif;font-size:.8em;',
    'box-shadow:0 4px 20px rgba(0,0,0,.7);min-width:200px;animation:nz-in .2s ease both;}',
    '#nz-keys kbd{background:#1A2E50;border-radius:4px;padding:1px 6px;color:#fff;font-family:monospace;font-size:.85em;}',

    /* PRINT */
    '@media print{.sticky-nav,.nuzu-bottom-nav,.breaking-banner,.waiting-room-section,',
    '#nz-tour-root,#nz-toast,.bookmark-btn,.share-btn,.src-key-bar,.top-stories-strip',
    '{display:none!important;}',
    'body,.cluster,.section-col-card{background:#fff!important;color:#000!important;}',
    '.title,h1,h2,h3,h4{color:#000!important;}',
    'a{color:#1E4FD8!important;text-decoration:underline!important;}',
    '.section-wrap{content-visibility:visible!important;}}',

    /* ── Solo-headline micro source favicon ── */
    '.hl-src-icon{display:inline-block;width:13px;height:13px;object-fit:contain;border-radius:3px;vertical-align:middle;margin-right:4px;margin-top:-2px;opacity:0.82;flex-shrink:0;}',
    '.src-label{display:inline-flex;align-items:center;gap:0;}',

    /* ── Section banner flash feedback (triggered by nav clicks) ── */
    /* Fires when a nav tab is tapped and the section is already in view,          */
    /* giving users clear visual confirmation their tap registered.                 */
    '@keyframes nz-sec-flash{0%{opacity:1}25%{opacity:0.55;background:rgba(30,79,216,0.16)}75%{opacity:0.85}100%{opacity:1}}',
    '.nz-sec-flash{animation:nz-sec-flash 0.6s ease both;}',

    /* ── Multi-step tutorial overlay ── */
    '#nuzu-onboard{position:fixed;inset:0;z-index:9999;background:rgba(2,9,18,0.97);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;font-family:"Inter",Arial,sans-serif;}',
    '.ob-card{background:#07111f;border:1px solid rgba(30,79,216,0.30);border-radius:16px;padding:28px 28px 22px;max-width:420px;width:100%;position:relative;box-shadow:0 8px 40px rgba(0,0,0,0.7),0 0 0 1px rgba(30,79,216,0.12);}',
    '.ob-step-dots{display:flex;gap:6px;justify-content:center;margin-bottom:20px;}',
    '.ob-step-dot{width:6px;height:6px;border-radius:50%;background:rgba(30,79,216,0.25);transition:all 0.2s;}',
    '.ob-step-dot.active{width:18px;border-radius:4px;background:#1E4FD8;}',
    '.ob-step-dot.done{background:rgba(30,79,216,0.55);}',
    '.ob-step{display:none;}.ob-step.visible{display:block;}',
    '.ob-icon-big{font-size:2.2em;margin-bottom:10px;text-align:center;}',
    '.ob-title{font-size:1.12em;font-weight:800;color:#fff;margin-bottom:6px;text-align:center;letter-spacing:0.01em;}',
    '.ob-subtitle{font-size:0.82em;color:#7EB3FF;text-align:center;margin-bottom:16px;line-height:1.55;}',
    '.ob-feature-list{list-style:none;padding:0;margin:0 0 16px;display:flex;flex-direction:column;gap:9px;}',
    '.ob-feature-list li{display:flex;align-items:flex-start;gap:10px;font-size:0.82em;color:#C8D8EE;line-height:1.45;}',
    '.ob-feature-list li .ob-li-icon{font-size:1.1em;flex-shrink:0;margin-top:1px;}',
    '.ob-vis-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:0 0 12px;}',
    '.ob-feed-mock{background:rgba(30,79,216,0.15);border:1px solid rgba(30,79,216,0.28);border-radius:6px;padding:7px 9px;font-size:0.82em;color:#a8c8ff;}',
    '.ob-live-dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:#22c55e;margin-right:5px;vertical-align:middle;animation:ob-pulse 1.5s ease-in-out infinite;}',
    '@keyframes ob-pulse{0%,100%{opacity:1}50%{opacity:0.3}}',
    '.ob-cluster-mock{border-left:4px solid #D97706;border-top:1px solid rgba(217,119,6,0.5);background:rgba(217,119,6,0.08);border-radius:0 5px 5px 0;padding:8px 10px;margin-bottom:12px;font-size:0.78em;color:#C8D8EE;}',
    '.ob-cluster-badge-mock{display:inline-block;background:linear-gradient(135deg,#78350F,#D97706);color:#FFF7ED;font-size:0.72em;padding:2px 7px;border-radius:8px;font-weight:bold;margin-bottom:6px;}',
    '.ob-badge-row{display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap;align-items:center;}',
    '.ob-badge-break{background:rgba(220,38,38,0.15);color:#f87171;border:1px solid rgba(220,38,38,0.35);font-size:0.7em;padding:2px 8px;border-radius:6px;font-weight:700;letter-spacing:0.06em;}',
    '.ob-badge-daily{background:rgba(30,79,216,0.15);color:#93c5fd;border:1px solid rgba(30,79,216,0.35);font-size:0.7em;padding:2px 8px;border-radius:6px;font-weight:700;letter-spacing:0.06em;}',
    '.ob-nav-row{display:flex;gap:8px;align-items:center;justify-content:space-between;margin-top:4px;}',
    '.ob-btn-primary{background:#1E4FD8;color:#fff;border:none;border-radius:8px;padding:11px 28px;font-size:0.92em;font-weight:700;cursor:pointer;letter-spacing:0.03em;font-family:"Inter",Arial,sans-serif;transition:background 0.15s;flex:1;}',
    '.ob-btn-primary:hover{background:#2563EB;}',
    '.ob-btn-prev{background:none;border:1px solid rgba(30,79,216,0.30);border-radius:8px;padding:11px 16px;font-size:0.88em;color:#4A6A99;cursor:pointer;font-family:"Inter",Arial,sans-serif;transition:border-color 0.15s,color 0.15s;}',
    '.ob-btn-prev:hover{border-color:#7EB3FF;color:#7EB3FF;}',
    '.onboard-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;width:100%;margin-bottom:18px;}',
    '.onboard-btn{background:rgba(30,79,216,0.10);border:2px solid rgba(30,79,216,0.28);border-radius:10px;padding:12px 8px;cursor:pointer;color:#C8D8EE;font-size:0.82em;font-weight:600;text-align:center;line-height:1.4;transition:all 0.15s;display:flex;flex-direction:column;align-items:center;gap:4px;font-family:"Inter",Arial,sans-serif;}',
    '.onboard-btn .ob-icon{font-size:1.45em;line-height:1;}',
    '.onboard-btn.selected{background:rgba(30,79,216,0.30);border-color:#1E4FD8;color:#fff;box-shadow:0 0 14px rgba(30,79,216,0.4);}',
    '.onboard-go{background:#1E4FD8;color:#fff;border:none;border-radius:8px;padding:12px 28px;font-size:0.94em;font-weight:700;cursor:pointer;letter-spacing:0.04em;font-family:"Inter",Arial,sans-serif;transition:background 0.15s;flex:1;}',
    '.onboard-go:hover{background:#2563EB;}',
    '.onboard-skip{margin-top:14px;background:none;border:none;color:#4A6A99;font-size:0.76em;cursor:pointer;text-decoration:underline;font-family:"Inter",Arial,sans-serif;display:block;text-align:center;width:100%;}',

    /* ── 3-day rating prompt ── */
    '#nuzu-rating-prompt{position:fixed;bottom:80px;left:50%;transform:translateX(-50%);z-index:8000;background:#07111f;border:1px solid rgba(30,79,216,0.35);border-radius:12px;padding:16px 20px;width:290px;box-shadow:0 6px 30px rgba(0,0,0,0.6);font-family:"Inter",Arial,sans-serif;display:none;}',
    '@keyframes nrp-up{from{opacity:0;transform:translateX(-50%) translateY(12px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}',
    '#nuzu-rating-prompt{animation:nrp-up 0.3s ease;}',
    '.nrp-title{font-size:0.92em;font-weight:700;color:#fff;margin-bottom:4px;}',
    '.nrp-sub{font-size:0.78em;color:#7EB3FF;margin-bottom:12px;}',
    '.nrp-stars{display:flex;gap:6px;margin-bottom:12px;}',
    '.nrp-star{font-size:1.5em;cursor:pointer;opacity:0.4;transition:opacity 0.15s,transform 0.1s;}',
    '.nrp-star:hover,.nrp-star.lit{opacity:1;}',
    '.nrp-star:hover{transform:scale(1.2);}',
    '.nrp-dismiss{background:none;border:none;color:#4A6A99;font-size:0.74em;cursor:pointer;text-decoration:underline;font-family:"Inter",Arial,sans-serif;}',

    /* ── Cluster visual enhancements (survive rebuilds via bundle) ── */
    /* Dark mode section tints */
    '#section-us .cluster{border-left-color:#C0392B!important;background:#1e0404!important;box-shadow:inset 4px 0 0 rgba(192,57,43,0.45),0 2px 10px rgba(0,0,0,0.4)!important;}',
    '#section-mideast .cluster{border-left-color:#D35400!important;background:#1c0900!important;box-shadow:inset 4px 0 0 rgba(211,84,0,0.42),0 2px 10px rgba(0,0,0,0.4)!important;}',
    '#section-world .cluster{border-left-color:#1A6FA8!important;background:#031120!important;box-shadow:inset 4px 0 0 rgba(26,111,168,0.42),0 2px 10px rgba(0,0,0,0.4)!important;}',
    '#section-tech .cluster{border-left-color:#1E4FD8!important;background:#030d22!important;box-shadow:inset 4px 0 0 rgba(30,79,216,0.42),0 2px 10px rgba(0,0,0,0.4)!important;}',
    '#section-business .cluster{border-left-color:#A07820!important;background:#181200!important;box-shadow:inset 4px 0 0 rgba(160,120,32,0.45),0 2px 10px rgba(0,0,0,0.4)!important;}',
    '#section-sports .cluster{border-left-color:#1A7A4A!important;background:#021407!important;box-shadow:inset 4px 0 0 rgba(26,122,74,0.42),0 2px 10px rgba(0,0,0,0.4)!important;}',
    '#section-culture .cluster{border-left-color:#9B3DB5!important;background:#160018!important;box-shadow:inset 4px 0 0 rgba(155,61,181,0.42),0 2px 10px rgba(0,0,0,0.4)!important;}',
    /* Light mode cluster tints */
    'body.light-mode #section-us .cluster{background:#FDE8E8!important;border-left-color:#C0392B!important;box-shadow:inset 4px 0 0 rgba(192,57,43,0.22),0 2px 8px rgba(192,57,43,0.08)!important;}',
    'body.light-mode #section-mideast .cluster{background:#FDEEDE!important;border-left-color:#D35400!important;box-shadow:inset 4px 0 0 rgba(211,84,0,0.22),0 2px 8px rgba(211,84,0,0.08)!important;}',
    'body.light-mode #section-world .cluster{background:#E4EFF8!important;border-left-color:#1A6FA8!important;box-shadow:inset 4px 0 0 rgba(26,111,168,0.22),0 2px 8px rgba(26,111,168,0.08)!important;}',
    'body.light-mode #section-tech .cluster{background:#E4EEFF!important;border-left-color:#1E4FD8!important;box-shadow:inset 4px 0 0 rgba(30,79,216,0.22),0 2px 8px rgba(30,79,216,0.08)!important;}',
    'body.light-mode #section-business .cluster{background:#F8F2DC!important;border-left-color:#A07820!important;box-shadow:inset 4px 0 0 rgba(160,120,32,0.22),0 2px 8px rgba(160,120,32,0.08)!important;}',
    'body.light-mode #section-sports .cluster{background:#E4F4EC!important;border-left-color:#1A7A4A!important;box-shadow:inset 4px 0 0 rgba(26,122,74,0.22),0 2px 8px rgba(26,122,74,0.08)!important;}',
    'body.light-mode #section-culture .cluster{background:#F3E4F8!important;border-left-color:#9B3DB5!important;box-shadow:inset 4px 0 0 rgba(155,61,181,0.22),0 2px 8px rgba(155,61,181,0.08)!important;}'

  ].join('');

  (function injectCSS() {
    var s = d.createElement('style');
    s.id = 'nz-bundle-css';
    s.textContent = HARDENING_CSS;
    d.head.appendChild(s);
  })();

  /* ═══════════════════════════════════════════════════════════════════════
     PART 2 — INJECT SECURITY META TAGS
     CSP, Referrer-Policy, X-Content-Type-Options.
     Note: On GitHub Pages _headers is ignored — these meta tags are
     the only working mechanism for security policies.
  ═══════════════════════════════════════════════════════════════════════ */
  (function injectSecurityMeta() {
    if (d.getElementById('nz-csp')) return;

    function meta(httpEquiv, content, name) {
      var m = d.createElement('meta');
      if (httpEquiv) m.httpEquiv = httpEquiv;
      if (name)      m.name      = name;
      m.content = content;
      return m;
    }

    var CSP = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' https://www.youtube.com https://www.youtube-nocookie.com https://fonts.googleapis.com",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "font-src 'self' https://fonts.gstatic.com",
      "frame-src https://www.youtube.com https://www.youtube-nocookie.com",
      "img-src 'self' data: https://www.google.com https://i.ytimg.com https://yt3.ggpht.com",
      "connect-src 'self' https://formspree.io",
      "object-src 'none'",
      "base-uri 'self'",
      "upgrade-insecure-requests"
    ].join('; ');

    var cspMeta = meta('Content-Security-Policy', CSP);
    cspMeta.id  = 'nz-csp';

    d.head.appendChild(cspMeta);
    d.head.appendChild(meta('X-Content-Type-Options', 'nosniff'));
    d.head.appendChild(meta(null, 'strict-origin-when-cross-origin', 'referrer'));
  })();

  /* ═══════════════════════════════════════════════════════════════════════
     PART 3 — PERFORMANCE LAYER
     Device detection, passive listener patcher, compositor hints,
     ResizeObserver-based equal-col-heights fix, idle scheduler,
     animation throttler for low-end devices.
  ═══════════════════════════════════════════════════════════════════════ */

  /* Device classification */
  var _mem  = navigator.deviceMemory || 4;
  var _cpu  = navigator.hardwareConcurrency || 4;
  var _conn = navigator.connection || {};
  var _slow = _conn.saveData || ['slow-2g','2g','3g'].includes(_conn.effectiveType);
  var _low  = _mem <= 2 || _cpu <= 2 || _slow;
  var _mid  = !_low && (_mem <= 4 || _cpu <= 4);
  if (_low)  d.documentElement.classList.add('nz-low');
  if (_mid)  d.documentElement.classList.add('nz-mid');
  if (_slow) d.documentElement.classList.add('nz-slow');

  /* Idle scheduler (requestIdleCallback with rAF fallback) */
  var _ric = w.requestIdleCallback
    ? function(cb,o){return w.requestIdleCallback(cb,o);}
    : function(cb){return setTimeout(function(){cb({timeRemaining:function(){return 50;},didTimeout:false});},16);};
  var _iq = [], _ir = false;
  function _drain(dl) {
    _ir = true;
    while(_iq.length && (dl.timeRemaining()>2||dl.didTimeout)){try{_iq.shift()();}catch(e){}}
    _iq.length ? _ric(_drain,{timeout:2000}) : (_ir=false);
  }
  function idle(fn, pri) {
    pri==='low' ? _iq.push(fn) : _iq.unshift(fn);
    if(!_ir) _ric(_drain,{timeout:pri==='low'?5000:2000});
  }

  /* Passive listener auto-patcher — must run before main script block */
  (function patchPassive() {
    var _orig = EventTarget.prototype.addEventListener;
    var _pe   = new Set(['scroll','touchstart','touchmove','touchend','wheel','mousewheel']);
    EventTarget.prototype.addEventListener = function(type, fn, opts) {
      if (_pe.has(type)) {
        if (opts==null)               opts = {passive:true};
        else if (typeof opts==='boolean') opts = {capture:opts,passive:true};
        else if (typeof opts==='object' && opts.passive==null) opts = Object.assign({},opts,{passive:true});
      }
      return _orig.call(this,type,fn,opts);
    };
    d.addEventListener('DOMContentLoaded', function() {
      setTimeout(function(){ EventTarget.prototype.addEventListener = _orig; }, 600);
    });
  })();

  /* ResizeObserver equal-col-heights fix — CORRECTED MEASUREMENT
   *
   * ROOT CAUSE OF REGRESSION: The previous version measured bCard height while
   * the container still had align-items:stretch active. With stretch, resetting
   * both card heights makes them BOTH expand to the taller of the two — so the
   * measured "bCard natural height" was actually max(bCard,rCard), which caused
   * rCard to be set to the wrong (too tall) value, breaking the balance.
   *
   * FIX: Temporarily set alignItems='flex-start' before measuring so bCard sits
   * at its true natural height. This mirrors the original nuzu_equalColHeights
   * implementation exactly. We also REPLACE nuzu_equalColHeights with this fixed
   * version (instead of a no-op) so all inline-script callers get the correct
   * implementation too.
   */
  (function fixEqualCols() {
    /* Core balance function — correct measurement via alignItems:flex-start */
    function doBalance() {
      if (w.innerWidth <= 900) return;
      d.querySelectorAll('.container.equal-cols').forEach(function(c) {
        var cols = c.querySelectorAll(':scope > .column');
        if (cols.length < 2) return;
        var b = cols[0].querySelector('.section-col-card');
        var r = cols[1] && cols[1].querySelector('.section-col-card');
        if (!b || !r) return;
        var wrap = c.closest('.section-columns');
        if (wrap && wrap.classList.contains('collapsed')) return;

        /* Reset both cards so we measure natural heights */
        b.style.height = b.style.maxHeight = b.style.minHeight = b.style.overflow = '';
        r.style.height = r.style.maxHeight = r.style.minHeight = r.style.overflow = '';

        /* Key fix: switch to flex-start so b sits at its OWN natural height,
           not stretched to match r. Force a reflow so the layout is committed. */
        var prevAlign = c.style.alignItems;
        c.style.alignItems = 'flex-start';
        void c.offsetHeight; /* synchronous reflow */

        var bH = Math.round(b.getBoundingClientRect().height);

        /* Restore align-items before writing styles (prevents visible flash) */
        c.style.alignItems = prevAlign;

        if (bH < 50) return; /* not yet painted — ResizeObserver will re-fire */

        /* Clip rCard to exactly bCard's natural height */
        r.style.height = r.style.maxHeight = bH + 'px';
        r.style.overflow = 'hidden';
      });
    }

    if (!w.ResizeObserver) {
      /* Fallback: just expose the fixed function; index.html setTimeouts handle timing */
      setTimeout(function(){ w.nuzu_equalColHeights = doBalance; }, 0);
      return;
    }

    /* ResizeObserver triggers doBalance on container size changes */
    var pending = new Set(), raf = null;
    function runBatch() { raf = null; if (pending.size) { pending.clear(); doBalance(); } }
    function queue(c) { pending.add(c); if (!raf) raf = requestAnimationFrame(runBatch); }

    function attach() {
      var ro = new ResizeObserver(function(es) {
        es.forEach(function(e) { queue(e.target); });
      });
      d.querySelectorAll('.container.equal-cols').forEach(function(c) {
        ro.observe(c); queue(c);
      });
      /* Replace nuzu_equalColHeights with the FIXED version (not a no-op).
         setTimeout(0) ensures this runs after the inline script defines it. */
      setTimeout(function() { w.nuzu_equalColHeights = doBalance; }, 0);
    }

    d.readyState === 'loading' ? d.addEventListener('DOMContentLoaded', attach) : attach();
  })();

  /* Compositor hints for sticky elements (non-low-end only) */
  function addHints() {
    if (_low) return;
    ['.sticky-nav','.nuzu-bottom-nav','.breaking-banner'].forEach(function(sel){
      var el=d.querySelector(sel);
      if(el && !el.style.willChange) el.style.willChange='transform';
    });
  }
  d.readyState==='loading' ? d.addEventListener('DOMContentLoaded',addHints) : addHints();

  /* Expose perf API */
  w.nuzuPerf = { idle: idle };

  /* ═══════════════════════════════════════════════════════════════════════
     PART 4 — SERVICE WORKER + UPDATE TOAST
     Registers SW and shows a non-intrusive bottom toast when a new
     version activates.
  ═══════════════════════════════════════════════════════════════════════ */
  (function initSW() {
    if (!('serviceWorker' in navigator)) return;

    function showToast() {
      if (d.getElementById('nz-toast') || performance.now() < 5000) return;
      var t = d.createElement('div');
      t.id = 'nz-toast';
      t.setAttribute('role','alert');
      t.setAttribute('aria-live','polite');
      t.innerHTML = '<span>🔄 NUZU updated</span>'
        +'<button id="nz-toast-ok">Reload</button>'
        +'<button id="nz-toast-x" aria-label="Dismiss">✕</button>';
      d.body.appendChild(t);
      requestAnimationFrame(function(){requestAnimationFrame(function(){t.classList.add('on');});});
      d.getElementById('nz-toast-ok').onclick = function(){w.location.reload();};
      d.getElementById('nz-toast-x').onclick  = function(){
        t.classList.remove('on');
        setTimeout(function(){if(t.parentNode)t.parentNode.removeChild(t);},350);
      };
      setTimeout(function(){t.classList.remove('on');},12000);
    }

    navigator.serviceWorker.register('/sw.js').catch(function(){});
    navigator.serviceWorker.addEventListener('controllerchange', showToast);
    navigator.serviceWorker.addEventListener('message', function(e){
      if(e.data && (e.data.type==='NUZU_SW_UPDATED' || e.data.type==='NUZU_UPDATE')) showToast();
    });
  })();

  /* ═══════════════════════════════════════════════════════════════════════
     PART 5 — ACCESSIBILITY LAYER
     Skip link, focus traps, ARIA improvements, keyboard shortcuts,
     aria-current on nav, screen reader announcer.
  ═══════════════════════════════════════════════════════════════════════ */

  /* Screen reader live region */
  var _srEl = null;
  function srSay(msg, pri) {
    if (!_srEl) {
      _srEl = d.createElement('div');
      _srEl.setAttribute('aria-live',pri||'polite');
      _srEl.setAttribute('aria-atomic','true');
      _srEl.style.cssText = 'position:absolute;left:-10000px;top:-10000px;width:1px;height:1px;overflow:hidden;';
      d.body.appendChild(_srEl);
    }
    if (pri) _srEl.setAttribute('aria-live',pri);
    _srEl.textContent = '';
    setTimeout(function(){_srEl.textContent=msg;},50);
  }

  /* Skip link */
  (function skipLink() {
    if (d.getElementById('nz-skip')) return;
    var a = d.createElement('a');
    a.id='nz-skip'; a.href='#nz-main'; a.textContent='Skip to main content';
    function ensureTarget() {
      if (!d.getElementById('nz-main')) {
        var el = d.querySelector('main,.section-wrap[id],#section-us');
        if (el) { el.id='nz-main'; el.setAttribute('tabindex','-1'); }
      }
    }
    d.readyState==='loading'
      ? d.addEventListener('DOMContentLoaded',function(){d.body.insertBefore(a,d.body.firstChild);ensureTarget();})
      : (d.body.insertBefore(a,d.body.firstChild), ensureTarget());
  })();

  /* Focus trap helpers */
  var _trap=null, _trapReturn=null;
  var _FQ='a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),[tabindex]:not([tabindex="-1"])';
  function trapFocus(el) {
    _trap=el; _trapReturn=d.activeElement;
    el.setAttribute('aria-modal','true');
    var foc=el.querySelectorAll(_FQ);
    if(foc.length) foc[0].focus();
  }
  function releaseTrap() {
    if(_trap) _trap.removeAttribute('aria-modal');
    _trap=null;
    if(_trapReturn && _trapReturn.focus) _trapReturn.focus();
    _trapReturn=null;
  }
  d.addEventListener('keydown',function(e){
    if(!_trap||e.key!=='Tab') return;
    var foc=Array.from(_trap.querySelectorAll(_FQ));
    if(!foc.length) return;
    if(e.shiftKey){if(d.activeElement===foc[0]){e.preventDefault();foc[foc.length-1].focus();}}
    else{if(d.activeElement===foc[foc.length-1]){e.preventDefault();foc[0].focus();}}
  });

  /* Watch overlays for open/close — attach trap */
  function watchOverlays() {
    var mo = new MutationObserver(function(muts){
      muts.forEach(function(m){
        var t=m.target;
        if(!t||!t.id) return;
        if(['wr-overlay','saved-panel','nuzu-onboard','nz-tour-root'].indexOf(t.id)<0) return;
        var open = t.style.display!=='none' && !t.classList.contains('hidden') && !t.hasAttribute('hidden');
        if(open && _trap!==t){ trapFocus(t); srSay('Panel opened. Press Escape to close.','assertive'); }
        else if(!open && _trap===t){ releaseTrap(); }
      });
    });
    ['wr-overlay','saved-panel'].forEach(function(id){
      var el=d.getElementById(id);
      if(el) mo.observe(el,{attributes:true,attributeFilter:['style','class','hidden']});
    });
  }

  /* ARIA improvements applied after DOM loads */
  function applyARIA() {
    var pairs=[
      ['.sticky-nav',    'navigation','Main navigation'],
      ['.nuzu-bottom-nav','navigation','Section navigation'],
      ['.search-bar-wrap','search',   null]
    ];
    pairs.forEach(function(p){
      var el=d.querySelector(p[0]);
      if(!el||el.getAttribute('role')) return;
      el.setAttribute('role',p[1]);
      if(p[2]) el.setAttribute('aria-label',p[2]);
    });

    var bb=d.querySelector('.breaking-banner');
    if(bb&&!bb.getAttribute('aria-live')){
      bb.setAttribute('aria-live','polite');
      bb.setAttribute('role','region');
      bb.setAttribute('aria-label','Breaking news');
    }

    var si=d.querySelector('.search-bar-wrap input');
    if(si&&!si.getAttribute('aria-label')) si.setAttribute('aria-label','Search all headlines');

    d.querySelectorAll('.section-wrap[id]').forEach(function(s){
      if(!s.getAttribute('role')) s.setAttribute('role','region');
      if(!s.getAttribute('aria-label')){
        var n=s.id.replace('section-','').replace('-',' ');
        s.setAttribute('aria-label',n.charAt(0).toUpperCase()+n.slice(1)+' News');
      }
    });

    var wr=d.getElementById('wr-fullscreen-btn');
    if(wr&&!wr.getAttribute('aria-label')) wr.setAttribute('aria-label','Open Waiting Room — live news video feeds');

    watchOverlays();
  }

  /* aria-current scroll spy — watch nav for .active class */
  function initScrollSpy() {
    function sync(){
      d.querySelectorAll('.sticky-nav-tabs .nav-tab-link,.nuzu-bottom-nav .bnav-item').forEach(function(l){
        l.classList.contains('nav-active')||l.classList.contains('active')
          ? l.setAttribute('aria-current','page')
          : l.removeAttribute('aria-current');
      });
    }
    var nav=d.querySelector('.sticky-nav-tabs,.nuzu-nav-tabs');
    if(nav) new MutationObserver(sync).observe(nav,{subtree:true,attributes:true,attributeFilter:['class']});
    sync();
  }

  /* Keyboard shortcuts */
  function initKeys() {
    var SECS={'1':'section-us','2':'section-world','3':'section-mideast','4':'section-tech','5':'section-business','6':'section-sports','7':'section-culture'};
    function typing(){var el=d.activeElement;return el&&(el.tagName==='INPUT'||el.tagName==='TEXTAREA'||el.isContentEditable);}
    d.addEventListener('keydown',function(e){
      if(e.ctrlKey||e.altKey||e.metaKey) return;
      if(e.key=='/'){
        if(typing()) return;
        e.preventDefault();
        var si=d.querySelector('.search-bar-wrap input,#nuzu-search-input');
        if(si){si.focus();si.select();}
      } else if(e.key==='w'||e.key==='W'){
        if(typing()) return;
        var b=d.getElementById('wr-fullscreen-btn'); if(b) b.click();
      } else if(e.key==='s'||e.key==='S'){
        if(typing()) return;
        var sb=d.querySelector('.saved-nav-btn,#bnav-saved-btn'); if(sb) sb.click();
      } else if(e.key==='?'&&!typing()){
        showKeys();
      } else if(SECS[e.key]&&!typing()){
        e.preventDefault();
        var se=d.getElementById(SECS[e.key]);
        if(se){se.scrollIntoView({behavior:'smooth',block:'start'});srSay('Jumped to '+e.key+' section');}
      }
    });

    function showKeys(){
      var ex=d.getElementById('nz-keys'); if(ex){ex.remove();return;}
      var shorts=[['/', 'Focus search'],['W','Waiting Room'],['S','Saved'],['1–7','Jump to section'],['?','Toggle shortcuts']];
      var box=d.createElement('div'); box.id='nz-keys';
      box.setAttribute('role','dialog'); box.setAttribute('aria-label','Keyboard shortcuts');
      var h='<div style="color:#7EB3FF;font-weight:700;margin-bottom:10px;">Keyboard Shortcuts</div>';
      shorts.forEach(function(p){
        h+='<div style="display:flex;justify-content:space-between;gap:16px;padding:3px 0;color:#A8C0E0;">'
         +'<kbd>'+p[0]+'</kbd><span>'+p[1]+'</span></div>';
      });
      box.innerHTML=h; d.body.appendChild(box);
      var timer=setTimeout(function(){if(box.parentNode)box.remove();},5000);
      setTimeout(function(){d.addEventListener('keydown',function rm(){clearTimeout(timer);box.remove();d.removeEventListener('keydown',rm);},{once:true});},100);
    }
  }

  d.readyState==='loading'
    ? d.addEventListener('DOMContentLoaded',function(){applyARIA();initScrollSpy();initKeys();})
    : (applyARIA(),initScrollSpy(),initKeys());

  w.nuzuA11y = { announce: srSay, trapFocus: trapFocus, releaseTrap: releaseTrap };

  /* ═══════════════════════════════════════════════════════════════════════
     PART 6 — ONBOARDING TOUR
     First-launch spotlight tour. Skippable. Replayable via nuzuTour.start().
     Waits for the existing interest picker to finish first.
  ═══════════════════════════════════════════════════════════════════════ */
  (function () {
    var TOUR_KEY     = 'nuzu_tour_v1';
    var INTEREST_KEY = 'nuzu_onboarded_v1';

    var STEPS = [
      {side:'center',title:'👋 Welcome to NUZU',body:'The dense, real-time news terminal. This 30-second tour shows you everything. Skip at any time — replay from the footer.',cta:'Show me around →',skip:'Skip tour'},
      {target:'.sticky-nav-tabs',side:'bottom',title:'📰 Section Tabs',body:'Tap US, World, Mid East, Tech, Business, Sports, or Culture to jump to that section instantly.'},
      {target:'.breaking-banner',side:'bottom',title:'🔴 Breaking Banner',body:'Live breaking headlines scroll here. Click any headline to go directly to that story.'},
      {target:'.top-stories-strip',side:'bottom',title:'⬆ Most Reported On',body:'Stories covered by 3+ sources rise here. The badge shows how many outlets are reporting on it.',scroll:true},
      {target:'.search-bar-wrap',side:'bottom',title:'🔍 Live Search',body:'Search any keyword to instantly filter all headlines across every section. Press Escape to clear.',scroll:true},
      {target:'.saved-nav-btn,.bnav-saved-btn',side:'bottom',title:'⭐ Save Articles',body:'Tap ★ next to any headline to save it. Saved articles persist across sessions and are available offline.'},
      {target:'#wr-fullscreen-btn,.wr-fullscreen-btn',side:'bottom',title:'▶ Waiting Room',body:'Fullscreen grid of 12 live news video streams from around the world. Muted by default. Press W anytime.',desktop:true},
      {target:'.light-toggle-wrap',side:'bottom',title:'⚙️ Appearance',body:'Use A+ / A− to adjust text size. 🌙 switches dark/light mode. All preferences are saved locally.'},
      {side:'center',title:'📲 Install NUZU',body:'Add NUZU to your home screen: on iOS tap Share → "Add to Home Screen". On Android tap ⋮ → "Install app". You get offline reading and fast launch.',cta:'Finish tour ✓',skip:null}
    ];

    function sg(k){try{return localStorage.getItem(k);}catch(_){return null;}}
    function ss(k,v){try{localStorage.setItem(k,v);}catch(_){}}
    function find(sel){if(!sel)return null;for(var p of sel.split(',')){var e=d.querySelector(p.trim());if(e&&e.getBoundingClientRect().width>0)return e;}return null;}

    var step=0, overlay=null, rect=null, active=false, mobile=w.innerWidth<=900;

    function filtered(){return STEPS.filter(function(s){return !(s.desktop&&mobile);});}

    function start(){
      if(d.getElementById('nuzu-onboard')){
        d.addEventListener('nuzuOnboardDismissed',function(){start();},{once:true});
        return;
      }
      step=0; active=true; mobile=w.innerWidth<=900;
      build(); show(0);
      w.addEventListener('keydown',onKey);
      w.addEventListener('resize',onResize);
    }

    function build(){
      teardown();
      var root=d.createElement('div'); root.id='nz-tour-root';
      var bd=d.createElement('div'); bd.id='nz-tour-bd';
      ['top','right','bottom','left'].forEach(function(s){var q=d.createElement('div');q.className='nz-quad';q.dataset.s=s;bd.appendChild(q);});
      var ring=d.createElement('div'); ring.id='nz-ring';
      var tip=d.createElement('div'); tip.id='nz-tip';
      root.appendChild(bd); root.appendChild(ring); root.appendChild(tip);
      d.body.appendChild(root);
      overlay=root;
      bd.addEventListener('click',advance);
    }

    var PAD=8;
    function spotlight(el){
      var ring=d.getElementById('nz-ring'), qs=d.querySelectorAll('.nz-quad'), vw=w.innerWidth, vh=w.innerHeight;
      if(!el){ring.style.opacity='0';qs[0].style.cssText='inset:0;display:block;';for(var i=1;i<qs.length;i++)qs[i].style.display='none';return;}
      var r=el.getBoundingClientRect();
      var x1=Math.max(0,r.left-PAD),y1=Math.max(0,r.top-PAD),x2=Math.min(vw,r.right+PAD),y2=Math.min(vh,r.bottom+PAD),w2=x2-x1,h2=y2-y1;
      ring.style.cssText='left:'+x1+'px;top:'+y1+'px;width:'+w2+'px;height:'+h2+'px;opacity:1;';
      var ss2=['top:0;left:0;right:0;height:'+y1+'px;display:block;','top:'+y1+'px;left:'+x2+'px;right:0;height:'+h2+'px;display:block;','top:'+y2+'px;left:0;right:0;bottom:0;display:block;','top:'+y1+'px;left:0;width:'+x1+'px;height:'+h2+'px;display:block;'];
      qs.forEach(function(q,i){q.style.cssText=ss2[i];});
      rect={x1:x1,y1:y1,x2:x2,y2:y2,w:w2,h:h2};
    }

    function tooltip(s){
      var tip=d.getElementById('nz-tip'); if(!tip)return;
      var vw=w.innerWidth, tipW=Math.min(320,vw-24), side=s.side||'bottom', left, top, GAP=14;
      if(side==='center'||!rect){
        tip.style.cssText='left:50%;top:50%;transform:translate(-50%,-50%);max-width:'+Math.min(340,vw-32)+'px;';
        return;
      }
      if(side==='bottom'){
        left=Math.max(12,Math.min(rect.x1+rect.w/2-tipW/2,vw-tipW-12));
        top=rect.y2+GAP;
        if(top+180>w.innerHeight) top=rect.y1-180-GAP;
      } else {
        left=Math.max(12,Math.min(rect.x1+rect.w/2-tipW/2,vw-tipW-12));
        top=rect.y1-180-GAP;
        if(top<8) top=rect.y2+GAP;
      }
      tip.style.cssText='left:'+left+'px;top:'+top+'px;width:'+tipW+'px;max-width:'+tipW+'px;transform:none;';
    }

    function renderTip(s, idx, total){
      var tip=d.getElementById('nz-tip'); if(!tip)return;
      var dots='<div class="nz-dots">';
      for(var i=0;i<total;i++) dots+='<span class="nz-dot'+(i<idx?' done':i===idx?' on':'')+'">';
      dots+='</div>';
      var skip=(s.skip!==null)?'<button class="nz-skip" id="nz-skip-btn">'+(s.skip||'Skip')+'</button>':'';
      tip.innerHTML=dots+'<h3>'+s.title+'</h3><p>'+s.body+'</p>'+'<div class="nz-btns"><button class="nz-cta" id="nz-cta">'+(s.cta||'Next →')+'</button>'+skip+'</div>';
      var cta=d.getElementById('nz-cta');if(cta)cta.onclick=function(e){e.stopPropagation();advance();};
      var sk=d.getElementById('nz-skip-btn');if(sk)sk.onclick=function(e){e.stopPropagation();finish(true);};
    }

    function show(idx){
      var steps=filtered(); if(idx>=steps.length){finish(false);return;}
      var s=steps[idx], el=s.target?find(s.target):null;
      if(el&&s.scroll!==false) el.scrollIntoView({behavior:'smooth',block:'center'});
      if(!overlay) build();
      setTimeout(function(){
        if(s.target) el=find(s.target);
        spotlight(el||null);
        tooltip(s);
        renderTip(s,idx,steps.length);
      },el&&s.scroll!==false?320:0);
    }

    function advance(){var steps=filtered();step++;step>=steps.length?finish(false):show(step);}
    function finish(skipped){ss(TOUR_KEY,'1');active=false;teardown();try{w.dispatchEvent(new CustomEvent('nuzuTourComplete',{detail:{skipped:skipped}}));}catch(_){}}
    function teardown(){var r=d.getElementById('nz-tour-root');if(r&&r.parentNode)r.parentNode.removeChild(r);overlay=null;rect=null;w.removeEventListener('keydown',onKey);w.removeEventListener('resize',onResize);}
    function onKey(e){if(!active)return;if(e.key==='Escape')finish(true);else if(e.key==='ArrowRight'||e.key==='Enter'||e.key===' '){e.preventDefault();advance();}else if(e.key==='ArrowLeft'&&step>0){step=Math.max(0,step-2);show(step);}}
    var _rt;function onResize(){clearTimeout(_rt);_rt=setTimeout(function(){mobile=w.innerWidth<=900;if(active)show(step);},150);}

    function maybeStart(){
      if(sg(TOUR_KEY)) return;
      if(!sg(INTEREST_KEY)){d.addEventListener('nuzuOnboardDismissed',function(){setTimeout(start,400);},{once:true});return;}
      setTimeout(start,600);
    }

    /* Detect when the existing interest picker (#nuzu-onboard) is removed */
    (function(){
      var _orig=Element.prototype.removeChild;
      Element.prototype.removeChild=function(child){
        if(child&&child.id==='nuzu-onboard'){
          Element.prototype.removeChild=_orig;
          setTimeout(function(){try{w.dispatchEvent(new CustomEvent('nuzuOnboardDismissed'));}catch(_){}},50);
        }
        return _orig.call(this,child);
      };
    })();

    w.nuzuTour={
      start:start,
      reset:function(){try{localStorage.removeItem(TOUR_KEY);}catch(_){}},
      hasRun:function(){return !!sg(TOUR_KEY);}
    };

    d.readyState==='loading'
      ? d.addEventListener('DOMContentLoaded',maybeStart)
      : maybeStart();
  })();


  /* ═══════════════════════════════════════════════════════════════════════
     PART 7 — CENTRALIZED NAV ROUTING (v3.2.0 — production fix)
     ─────────────────────────────────────────────────────────────────────
     ROOT CAUSE OF US TAB BUG (confirmed via code audit):
     ─────────────────────────────────────────────────────────────────────
     1. stopImmediatePropagation() in the old v3.1 capture handler blocked
        the inline index.html handler, making the bundle the SOLE router.

     2. When #section-us is already near the viewport top (the most common
        state on fresh load), the old handler computed:
          targetY = pageYOffset + rect.top - navH - 2  →  ≈ 0
        then called scrollTo({top:0}) which the browser silently ignores
        when already at y=0. Result: the US tab visibly "does nothing".

     3. Other sections (World, Tech, …) escape this bug because they are
        further down the page and the scroll produces visible movement.

     FIX — three-pronged:
     ─────────────────────────────────────────────────────────────────────
     A. stopImmediatePropagation REMOVED. Both this handler and the inline
        index.html handler now coexist. Both call the same _nz_scroll
        (scrollIntoView) — harmless double-call; browser deduplicates.

     B. "Already near top" case now calls scrollTo({top:0}) AND forces a
        layout-flush scroll by scrolling to y=1 first then back to y=0,
        guaranteeing a browser-visible scroll event even when already at top.

     C. Section banner flash (.nz-sec-flash animation) added as visual
        feedback so users always see confirmation their tap registered,
        even when the page doesn't scroll because they're already there.

     D. Section collapse guard: if the target section was collapsed by the
        user, it is automatically expanded before scrolling, so the scroll
        target is never hidden.
  ═══════════════════════════════════════════════════════════════════════ */
  (function() {

    /* ── Flash the section banner for visual tap confirmation ── */
    function flashBanner(sectionEl) {
      if (!sectionEl) return;
      var banner = sectionEl.querySelector('.section-banner');
      if (!banner) return;
      banner.classList.remove('nz-sec-flash');
      void banner.offsetWidth; /* force reflow so animation restarts cleanly */
      banner.classList.add('nz-sec-flash');
      setTimeout(function() { banner.classList.remove('nz-sec-flash'); }, 700);
    }

    /* ── Expand section if collapsed ── */
    function expandSection(sectionEl) {
      if (!sectionEl) return;
      var cols = sectionEl.querySelector('.section-columns');
      if (cols && cols.classList.contains('collapsed')) {
        cols.classList.remove('collapsed');
        var btn = d.querySelector('[data-target="' + cols.id + '"]');
        if (btn) btn.innerHTML = '&#9660;';
      }
    }

    /* ── Canonical scroll-to-section with forced response ──
     *
     * scrollIntoView with block:'start' is the correct method here because
     * it respects scroll-margin-top AND forces layout on content-visibility:auto
     * sections. HOWEVER it is a silent no-op when the element is already "at
     * start". We detect that case and force a micro-scroll to guarantee a
     * browser-visible scroll event, then flash the banner regardless.
     */
    function scrollToSection(el) {
      if (!el) return;
      expandSection(el);

      var navEl = d.querySelector('.sticky-nav');
      var navH  = navEl ? navEl.getBoundingClientRect().height : 54;
      var rect  = el.getBoundingClientRect();

      /* "Already there" threshold: the section top is within navH+10px of viewport top */
      var alreadyAtSection = rect.top >= 0 && rect.top <= navH + 10;

      if (alreadyAtSection && w.pageYOffset < 10) {
        /* Section is at the very top of the page and we are too.
           Force a micro-scroll (y=2 then y=0) so the browser registers
           movement, then snap back to true top. */
        w.scrollTo({ top: 2, behavior: 'instant' });
        requestAnimationFrame(function() {
          w.scrollTo({ top: 0, behavior: 'smooth' });
        });
      } else if (typeof w._nz_scroll === 'function') {
        /* scrollIntoView — handles content-visibility:auto correctly */
        w._nz_scroll(el, 'smooth');
      } else {
        /* Fallback for very early calls before _nz_scroll is defined */
        var targetY = Math.max(0, w.pageYOffset + rect.top - navH - 2);
        w.scrollTo({ top: targetY, behavior: 'smooth' });
      }

      /* Always flash the section banner as visual confirmation */
      flashBanner(el);
    }

    /* ── Install capture-phase handler for sticky nav tabs ──
     *
     * Capture phase fires BEFORE element-level handlers. We call
     * preventDefault() to suppress native hash navigation but we do NOT
     * call stopImmediatePropagation() — the inline index.html handler
     * is allowed to also fire. Both call the same scroll function;
     * the browser deduplicates identical smooth-scroll commands.
     */
    function navFix() {
      d.addEventListener('click', function(e) {
        /* Find the clicked nav link (handles clicks on child elements too) */
        var link = e.target.closest
          ? e.target.closest('.sticky-nav a.nav-link[href^="#"]')
          : null;
        if (!link) {
          /* Fallback for browsers without Element.closest() */
          var t = e.target;
          while (t && t !== d.body) {
            if (t.matches && t.matches('.sticky-nav a.nav-link[href^="#"]')) { link = t; break; }
            t = t.parentNode;
          }
        }
        if (!link) return;

        var sectionId = (link.getAttribute('href') || '').replace(/^#/, '');
        if (!sectionId) return;
        var el = d.getElementById(sectionId);
        if (!el) return;

        e.preventDefault();
        /* NOTE: stopImmediatePropagation intentionally removed (see PART 7 header) */

        scrollToSection(el);
      }, true); /* capture = true: fires before bubble-phase element handlers */

      /* ── Bottom nav: add flash feedback (scroll is already handled inline) ── */
      d.querySelectorAll('.nuzu-bottom-nav-item[data-section]').forEach(function(item) {
        item.addEventListener('click', function() {
          var sectionId = item.getAttribute('data-section');
          if (!sectionId) return;
          var el = d.getElementById(sectionId);
          if (el) {
            expandSection(el);
            flashBanner(el);
          }
        });
      });
    }

    d.readyState === 'loading'
      ? d.addEventListener('DOMContentLoaded', navFix)
      : navFix();
  })();


  /* ═══════════════════════════════════════════════════════════════════════
     PART 8 — MULTI-STEP FEATURE TUTORIAL + COMPLETION FLAG SYSTEM
     Replaces the simple interest picker with a 5-step guided tutorial.
     All localStorage flags are set BEFORE any animations to guarantee
     the tutorial never re-shows on any future visit.
     Flags: nuzu_onboarded_v2, nuzu_interests_set, nuzu_onboarded_v1
  ═══════════════════════════════════════════════════════════════════════ */
  (function() {
    function sg(k){try{return localStorage.getItem(k);}catch(_){return null;}}
    function ss(k,v){try{localStorage.setItem(k,v);}catch(_){}}

    // Triple-flag guard — any one set = skip permanently
    if (sg('nuzu_onboarded_v2') || sg('nuzu_interests_set')) return;

    var STEPS = [
      {
        icon: '📡',
        title: 'Welcome to NUZU News',
        subtitle: 'Real news in real time — 200+ trusted sources, refreshed every hour.',
        html: function() {
          return '<ul class="ob-feature-list">'
            + '<li><span class="ob-li-icon">🗂️</span><span><strong>7 live sections</strong> — US, World, Middle East, Tech, Business, Sports, Culture</span></li>'
            + '<li><span class="ob-li-icon">⚡</span><span><strong>Multi-source clustering</strong> groups related stories so you see the full picture</span></li>'
            + '<li><span class="ob-li-icon">📺</span><span><strong>Waiting Room mode</strong> turns NUZU into a live multi-channel news wall</span></li>'
            + '<li><span class="ob-li-icon">🌗</span><span><strong>Light/Dark mode</strong>, font size, and saved articles — all stored on your device</span></li>'
            + '</ul>';
        }
      },
      {
        icon: '📺',
        title: 'Waiting Room — Your News Command Center',
        subtitle: 'Leave multiple live feeds open at once — like cable news, but you choose every channel.',
        html: function() {
          return '<div class="ob-vis-grid">'
            + '<div class="ob-feed-mock"><span class="ob-live-dot"></span>U.S. Live</div>'
            + '<div class="ob-feed-mock"><span class="ob-live-dot"></span>Markets Live</div>'
            + '<div class="ob-feed-mock"><span class="ob-live-dot"></span>World Live</div>'
            + '<div class="ob-feed-mock"><span class="ob-live-dot"></span>Tech Live</div>'
            + '</div>'
            + '<ul class="ob-feature-list" style="margin-top:12px">'
            + '<li><span class="ob-li-icon">🎯</span><span>Monitor breaking news, markets, geopolitics, and sports <strong>simultaneously</strong></span></li>'
            + '<li><span class="ob-li-icon">🔇</span><span>Feeds start muted — click any to unmute. No autoplay chaos.</span></li>'
            + '<li><span class="ob-li-icon">⌨️</span><span>Press <strong>W</strong> to enter Waiting Room. Press <strong>ESC</strong> to exit.</span></li>'
            + '</ul>';
        }
      },
      {
        icon: '🔗',
        title: 'Story Clustering — See the Full Picture',
        subtitle: 'When multiple outlets cover the same story, NUZU collapses them into one node.',
        html: function() {
          return '<div class="ob-cluster-mock">'
            + '<div class="ob-cluster-badge-mock">4 SOURCES</div>'
            + '<div style="font-size:0.85em;font-weight:600;color:#fff;margin-bottom:4px">Federal Reserve raises rates amid inflation concerns</div>'
            + '<div style="font-size:0.74em;color:#7EB3FF">AP · Reuters · WSJ · Bloomberg ▾ tap to expand</div>'
            + '</div>'
            + '<ul class="ob-feature-list">'
            + '<li><span class="ob-li-icon">📰</span><span><strong>Fewer duplicates</strong> — one event, one node, multiple perspectives inside</span></li>'
            + '<li><span class="ob-li-icon">🔽</span><span>Tap a cluster to <strong>expand</strong> all sources. Tap again to collapse.</span></li>'
            + '<li><span class="ob-li-icon">🏆</span><span><strong>More sources = more corroborated</strong> — the badge tells you immediately</span></li>'
            + '</ul>';
        }
      },
      {
        icon: '🚨',
        title: 'Breaking vs. Daily Headlines',
        subtitle: 'NUZU automatically distinguishes urgency so you scan smarter.',
        html: function() {
          return '<div class="ob-badge-row"><span class="ob-badge-break">🔴 BREAKING</span>'
            + '<span style="font-size:0.78em;color:#C8D8EE;line-height:2;margin-left:8px">High source velocity · Active major event</span></div>'
            + '<div class="ob-badge-row" style="margin-top:8px"><span class="ob-badge-daily">📰 DAILY</span>'
            + '<span style="font-size:0.78em;color:#C8D8EE;line-height:2;margin-left:8px">Ongoing story · Broader coverage</span></div>'
            + '<div style="margin-top:14px;font-size:0.78em;color:#7EB3FF;font-weight:600">Source reliability pips:</div>'
            + '<div style="display:flex;gap:8px;margin-top:6px;font-size:0.76em;color:#C8D8EE;flex-wrap:wrap">'
            + '<span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#22c55e;margin-right:4px;vertical-align:middle"></span>Tier 1 — AP, Reuters, BBC</span>'
            + '<span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#f59e0b;margin-right:4px;vertical-align:middle"></span>Tier 2 — Major regional</span>'
            + '<span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#6b7280;margin-right:4px;vertical-align:middle"></span>Tier 3 — Syndicated</span>'
            + '</div>';
        }
      },
      {
        icon: '🎯',
        title: 'Personalize Your Feed',
        subtitle: 'Pick your interests. NUZU surfaces your sections first. Your answer is saved permanently.',
        html: function() {
          var OPTS = [
            {id:'us',icon:'🇺🇸',label:'US Politics'},
            {id:'mideast',icon:'🌍',label:'Middle East'},
            {id:'tech',icon:'💻',label:'Tech & AI'},
            {id:'sports',icon:'🏆',label:'Sports'},
            {id:'business',icon:'💰',label:'Business'},
            {id:'culture',icon:'🎬',label:'Culture'}
          ];
          var g = '<div class="onboard-grid" id="ob-grid">';
          OPTS.forEach(function(o) {
            g += '<button class="onboard-btn" data-id="' + o.id + '"><span class="ob-icon">' + o.icon + '</span>' + o.label + '</button>';
          });
          g += '</div>';
          return g;
        }
      }
    ];

    var currentStep = 0;
    var sel = {};
    var ov = d.createElement('div');
    ov.id = 'nuzu-onboard';

    function renderStep() {
      var s = STEPS[currentStep];
      var isLast  = currentStep === STEPS.length - 1;
      var isFirst = currentStep === 0;

      var dots = '<div class="ob-step-dots">';
      STEPS.forEach(function(_, i) {
        var cls = i < currentStep ? 'done' : (i === currentStep ? 'active' : '');
        dots += '<div class="ob-step-dot ' + cls + '"></div>';
      });
      dots += '</div>';

      var prevBtn  = !isFirst ? '<button class="ob-btn-prev" id="ob-prev">← Back</button>' : '';
      var nextLabel = isLast ? 'Save & Enter NUZU →' : 'Next →';
      var nextCls   = isLast ? 'onboard-go' : 'ob-btn-primary';

      var card = ov.querySelector('.ob-card');
      if (!card) { card = d.createElement('div'); card.className = 'ob-card'; ov.appendChild(card); }

      card.innerHTML = dots
        + '<div class="ob-step visible">'
        + '<div class="ob-icon-big">' + s.icon + '</div>'
        + '<div class="ob-title">' + s.title + '</div>'
        + '<div class="ob-subtitle">' + s.subtitle + '</div>'
        + s.html()
        + '</div>'
        + '<div class="ob-nav-row">' + prevBtn + '<button class="' + nextCls + '" id="ob-next">' + nextLabel + '</button></div>'
        + '<button class="onboard-skip" id="ob-skip">Skip intro &amp; see everything</button>';

      // Bind interest grid if last step
      if (isLast) {
        card.querySelectorAll('#ob-grid .onboard-btn').forEach(function(btn) {
          if (sel[btn.getAttribute('data-id')]) btn.classList.add('selected');
          btn.addEventListener('click', function() {
            var id = btn.getAttribute('data-id');
            if (sel[id]) { delete sel[id]; btn.classList.remove('selected'); }
            else          { sel[id] = 1;   btn.classList.add('selected'); }
          });
        });
      }

      var prevEl = card.querySelector('#ob-prev');
      if (prevEl) prevEl.addEventListener('click', function() { currentStep = Math.max(0, currentStep - 1); renderStep(); });

      card.querySelector('#ob-next').addEventListener('click', function() {
        if (isLast) finish(); else { currentStep++; renderStep(); }
      });
      card.querySelector('#ob-skip').addEventListener('click', function() { sel = {}; finish(); });
    }

    function finish() {
      // Write ALL flags BEFORE any animation — belt and suspenders
      try {
        var order = Object.keys(sel);
        if (!order.length) order = ['us','mideast','tech','sports','business','culture'];
        ss('nuzu_interest_order', JSON.stringify(order));
        ss('nuzu_onboarded_v1',  '1');
        ss('nuzu_onboarded_v2',  '1');
        ss('nuzu_interests_set', '1');  // dedicated completion flag for interest picker
        if (!sg('nuzu_first_visit')) ss('nuzu_first_visit', Date.now().toString());
      } catch(_) {}

      // Brief "all set" confirmation then fade
      var card = ov.querySelector('.ob-card');
      if (card) {
        card.innerHTML = '<div style="text-align:center;padding:32px 0">'
          + '<div style="font-size:2.6em;margin-bottom:12px">✅</div>'
          + '<div style="font-size:1.1em;font-weight:800;color:#fff;margin-bottom:8px">You\'re all set!</div>'
          + '<div style="font-size:0.82em;color:#7EB3FF;line-height:1.6">Preferences saved permanently.<br>You won\'t be asked again.</div>'
          + '</div>';
      }

      try { w.dispatchEvent(new w.CustomEvent('nuzuOnboardDismissed')); } catch(_) {}

      setTimeout(function() {
        ov.style.transition = 'opacity 0.4s';
        ov.style.opacity    = '0';
        setTimeout(function() { if (ov.parentNode) ov.parentNode.removeChild(ov); }, 440);
      }, 900);
    }

    // Also seed first_visit for returning users who skipped the old tutorial
    if (!sg('nuzu_first_visit')) ss('nuzu_first_visit', Date.now().toString());

    function launch() {
      // Remove any existing simple picker rendered by bot.py so we don't double-show
      var existing = d.getElementById('nuzu-onboard');
      if (existing && existing !== ov && existing.parentNode) existing.parentNode.removeChild(existing);

      renderStep();
      d.body.insertBefore(ov, d.body.firstChild);
    }

    d.readyState === 'loading'
      ? d.addEventListener('DOMContentLoaded', launch)
      : launch();
  })();


  /* ═══════════════════════════════════════════════════════════════════════
     PART 9 — 3-DAY RATING PROMPT
     Shows once after 72h of first visit. Dismissing snoozes 14 days.
     Completing a star rating sets nuzu_rated permanently — never shows again.
  ═══════════════════════════════════════════════════════════════════════ */
  (function() {
    function sg(k){try{return localStorage.getItem(k);}catch(_){return null;}}
    function ss(k,v){try{localStorage.setItem(k,v);}catch(_){}}

    function maybeShowRating() {
      if (sg('nuzu_rated')) return;
      var fv = parseInt(sg('nuzu_first_visit') || '0', 10);
      if (!fv) return;
      if (Date.now() - fv < 72 * 60 * 60 * 1000) return;
      var dismissed = parseInt(sg('nuzu_rate_dismissed') || '0', 10);
      if (dismissed && (Date.now() - dismissed) < 14 * 24 * 60 * 60 * 1000) return;

      var prompt = d.createElement('div');
      prompt.id = 'nuzu-rating-prompt';
      prompt.innerHTML = '<div class="nrp-title">Enjoying NUZU? ⭐</div>'
        + '<div class="nrp-sub">Help us improve with a quick rating:</div>'
        + '<div class="nrp-stars" id="nrp-stars">'
        + '<span class="nrp-star" data-v="1">★</span><span class="nrp-star" data-v="2">★</span>'
        + '<span class="nrp-star" data-v="3">★</span><span class="nrp-star" data-v="4">★</span>'
        + '<span class="nrp-star" data-v="5">★</span></div>'
        + '<button class="nrp-dismiss" id="nrp-dismiss">Remind me later</button>';

      d.body.appendChild(prompt);
      setTimeout(function() { prompt.style.display = 'block'; }, 2500);

      var stars = prompt.querySelectorAll('.nrp-star');
      stars.forEach(function(star) {
        star.addEventListener('mouseenter', function() {
          var v = parseInt(star.getAttribute('data-v'));
          stars.forEach(function(s, i) { s.classList.toggle('lit', i < v); });
        });
        star.addEventListener('mouseleave', function() { stars.forEach(function(s) { s.classList.remove('lit'); }); });
        star.addEventListener('click', function() {
          ss('nuzu_rated', '1');
          prompt.innerHTML = '<div class="nrp-title">Thanks! 🎉</div><div class="nrp-sub">Your feedback helps us improve.</div>';
          setTimeout(function() {
            prompt.style.transition = 'opacity 0.35s';
            prompt.style.opacity = '0';
            setTimeout(function() { if (prompt.parentNode) prompt.parentNode.removeChild(prompt); }, 380);
          }, 2000);
        });
      });

      d.getElementById('nrp-dismiss').addEventListener('click', function() {
        ss('nuzu_rate_dismissed', Date.now().toString());
        prompt.style.transition = 'opacity 0.3s';
        prompt.style.opacity = '0';
        setTimeout(function() { if (prompt.parentNode) prompt.parentNode.removeChild(prompt); }, 320);
      });
    }

    d.readyState === 'loading'
      ? d.addEventListener('DOMContentLoaded', function() { setTimeout(maybeShowRating, 3000); })
      : setTimeout(maybeShowRating, 3000);
  })();


  /* ═══════════════════════════════════════════════════════════════════════
     PART 10 — SOLO HEADLINE MICRO-FAVICONS
     Clusters already render a .nuzu-thumb logo image. Standalone .headline
     rows only have a coloured pip + text src-label. This injects a 13px
     favicon <img> before the source name for known outlets, using the same
     icon path + Google favicon fallback chain the cluster system uses.
     Additive only — no DOM mutation beyond a single img insert per headline.
  ═══════════════════════════════════════════════════════════════════════ */
  (function() {
    var DOMAIN_MAP = {
      'AP':'apnews.com','NPR':'npr.org','BBC':'bbc.com','Reuters':'reuters.com',
      'NYT':'nytimes.com','WaPo':'washingtonpost.com','Guardian':'theguardian.com',
      'Politico':'politico.com','CNN':'cnn.com','Fox News':'foxnews.com',
      'MSNBC':'msnbc.com','CBS News':'cbsnews.com','NBC News':'nbcnews.com',
      'ABC News':'abcnews.go.com','Bloomberg':'bloomberg.com','WSJ':'wsj.com',
      'Axios':'axios.com','Vox':'vox.com','Time':'time.com','Forbes':'forbes.com',
      'Fortune':'fortune.com','Business Insider':'businessinsider.com','CNBC':'cnbc.com',
      'MarketWatch':'marketwatch.com','The Hill':'thehill.com','HuffPost':'huffpost.com',
      'Slate':'slate.com','The Atlantic':'theatlantic.com','Wired':'wired.com',
      'Ars Technica':'arstechnica.com','TechCrunch':'techcrunch.com',
      'Verge':'theverge.com','Engadget':'engadget.com','Mashable':'mashable.com',
      'Gizmodo':'gizmodo.com','ESPN':'espn.com','FOX Sports':'foxsports.com',
      'Yahoo Sports':'sports.yahoo.com','Sports Illustrated':'si.com',
      'The Athletic':'theathletic.com','Rolling Stone':'rollingstone.com',
      'Billboard':'billboard.com','Variety':'variety.com',
      'Hollywood Reporter':'hollywoodreporter.com','Deadline':'deadline.com',
      'IMDb':'imdb.com','Vogue':'vogue.com','GQ':'gq.com','Brookings':'brookings.edu',
      'BBC News':'bbc.com','MSN':'msn.com','Yahoo News':'yahoo.com',
      'USA Today':'usatoday.com','Newsweek':'newsweek.com','The Week':'theweek.com',
      'Vice':'vice.com','New Yorker':'newyorker.com','Salon':'salon.com',
      'Aljazeera':'aljazeera.com','Al Jazeera':'aljazeera.com',
      'Times of India':'timesofindia.com','The Times':'thetimes.com',
      'Daily Mail':'dailymail.co.uk','Independent':'independent.co.uk',
      'Sky News':'skynews.com','Deutsche Welle':'dw.com','DW':'dw.com',
      'France 24':'france24.com','Le Monde':'lemonde.fr','Spiegel':'spiegel.de'
    };

    var VER = '2026051820'; // bump version to bypass any cached 404s

    function injectIcons() {
      d.querySelectorAll('.headline').forEach(function(hl) {
        if (hl.querySelector('.hl-src-icon')) return; // already done
        var srcLabel = hl.querySelector('.src-label');
        if (!srcLabel) return;
        var raw    = (srcLabel.textContent || '').replace(/^[\s\u2014\-]+/, '').trim();
        var domain = DOMAIN_MAP[raw];
        if (!domain) return;

        var img = d.createElement('img');
        img.className = 'hl-src-icon';
        img.src = 'icons/sources/' + domain + '.png?v=' + VER;
        img.alt = '';
        img.loading   = 'lazy';
        img.decoding  = 'async';
        img.setAttribute('referrerpolicy', 'no-referrer');
        img.dataset.domain = domain;
        img.onerror = function() {
          if (!img.dataset.tried) {
            img.dataset.tried = '1';
            img.src = 'https://www.google.com/s2/favicons?domain=' + domain + '&sz=32';
          } else {
            img.style.display = 'none';
          }
        };
        srcLabel.insertBefore(img, srcLabel.firstChild);
      });
    }

    d.readyState === 'loading'
      ? d.addEventListener('DOMContentLoaded', injectIcons)
      : injectIcons();
  })();


}(window, document));
