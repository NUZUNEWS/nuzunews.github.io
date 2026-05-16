/**
 * NUZU News — Production Bundle
 * Includes: Performance · Accessibility · Onboarding Tour · Mobile Hardening · Security
 *
 * This is a SINGLE DROP-IN FILE. No other JS/CSS files needed.
 * bot_patch.py adds one <script> tag to bot.py that loads this file.
 * That's the entire front-end install.
 *
 * Version: 3.0.0
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
    '.section-wrap{content-visibility:visible!important;}}'
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

  /* ResizeObserver equal-col-heights fix (replaces 4× setTimeout + img-load reflows) */
  (function fixEqualCols() {
    if (!w.ResizeObserver) return;
    var pending = new Set(), raf = null;
    function run() {
      raf = null;
      if (w.innerWidth <= 900) return;
      var measures = [];
      pending.forEach(function(c) {
        var cols = c.querySelectorAll(':scope > .column');
        if (cols.length < 2) return;
        var b = cols[0].querySelector('.section-col-card'), r = cols[1] && cols[1].querySelector('.section-col-card');
        if (!b||!r) return;
        var wrap = c.closest('.section-columns');
        if (wrap && wrap.classList.contains('collapsed')) return;
        b.style.height = b.style.maxHeight = b.style.overflow = '';
        r.style.height = r.style.maxHeight = r.style.overflow = '';
        measures.push({b:b,r:r});
      });
      pending.clear();
      if (!measures.length) return;
      requestAnimationFrame(function() {
        var hs = measures.map(function(m){return Math.round(m.b.getBoundingClientRect().height);});
        measures.forEach(function(m,i){
          if(hs[i]<50) return;
          m.r.style.height = m.r.style.maxHeight = hs[i]+'px';
          m.r.style.overflow = 'hidden';
        });
      });
    }
    function queue(c){pending.add(c);if(!raf)raf=requestAnimationFrame(run);}
    function attach() {
      var ro = new ResizeObserver(function(es){es.forEach(function(e){queue(e.target);});});
      d.querySelectorAll('.container.equal-cols').forEach(function(c){ro.observe(c);queue(c);});
      /* Disable old function after it's had a chance to be defined */
      setTimeout(function(){
        try{Object.defineProperty(w,'nuzu_equalColHeights',{value:function(){},writable:false,configurable:true});}
        catch(_){w.nuzu_equalColHeights=function(){};}
      },0);
    }
    d.readyState==='loading' ? d.addEventListener('DOMContentLoaded',attach) : attach();
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
      if(e.key==='/'){
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
      for(var i=0;i<total;i++) dots+='<span class="nz-dot'+(i<idx?' done':i===idx?' on':'')+'"></span>';
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

}(window, document));
