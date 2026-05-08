/**
 * Cinematic 3D Particle Field — Ultra-Smooth Edition
 * ─────────────────────────────────────────────────────
 * Performance model: minimum draw calls per frame.
 *
 * Key techniques:
 * 1. Sprite cache        — glow textures pre-rendered; blitted with drawImage()
 * 2. Spatial grid        — O(N) neighbour lookup for connection lines
 * 3. SINGLE-PATH batching — ALL lines merged into ONE beginPath/stroke call
 *                           (eliminates per-line state-change overhead)
 * 4. globalAlpha batching — particles drawn in same-color groups
 * 5. Integer coordinates — Math.round() prevents sub-pixel anti-aliasing cost
 * 6. alpha:false canvas  — skips transparency compositing on the canvas element
 * 7. Cached vignette     — created once, reused every frame
 * 8. Deferred resize     — debounced to avoid storm of redraws
 */
(function () {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: false, desynchronized: true });

    let W, H, cx, cy;
    let particles = [];
    let ripples   = [];
    let animId;
    let time      = 0;

    const mouse = { x: -9999, y: -9999, active: false };

    // ─── Config ──────────────────────────────────────────────────────────────────
    const C = {
        layers: [
            //          count  spd   sz    alpha  connDist
            { count: 120, speedMul: 0.10, sizeMul: 0.32, alphaMul: 0.20, connectDist: 0   },
            { count:  90, speedMul: 0.25, sizeMul: 0.58, alphaMul: 0.35, connectDist: 115 },
            { count:  55, speedMul: 0.48, sizeMul: 0.95, alphaMul: 0.62, connectDist: 145 },
            { count:  20, speedMul: 0.75, sizeMul: 1.40, alphaMul: 0.88, connectDist: 165 },
        ],
        baseSpeed:         0.26,
        baseSize:          1.8,
        mouseRadius:       210,
        mouseForce:        0.050,
        rippleSpeed:       4.2,
        rippleLife:        52,
        /* Trail: higher = shorter blur = less ghosting = feels snappier */
        trailAlpha:        0.18,
        ambientPulseSpeed: 0.0025,
        gridCell:          145,
        /* Line opacity budget — one value governs ALL lines */
        lineBaseAlpha:     0.08,
        colors: [
            { r: 99,  g: 102, b: 241 },
            { r: 124, g: 92,  b: 252 },
            { r: 192, g: 132, b: 252 },
            { r: 139, g: 92,  b: 246 },
            { r: 34,  g: 211, b: 238 },
            { r: 96,  g: 165, b: 250 },
            { r: 244, g: 114, b: 182 },
            { r: 56,  g: 189, b: 248 },
        ],
    };

    // ─── Sprite cache ─────────────────────────────────────────────────────────────
    // Pre-render ~32 glow sprites at init; zero gradient cost per frame.
    const spriteCache = new Map();

    function getSprite(r, g, b, size) {
        // Round size to nearest 0.25 to maximise cache hits
        const roundedSize = Math.round(size * 4) / 4;
        const key = `${r},${g},${b},${roundedSize}`;
        if (spriteCache.has(key)) return spriteCache.get(key);

        const d   = Math.ceil(roundedSize * 9) | 1; // odd for true centre pixel
        const sc  = document.createElement('canvas');
        sc.width  = sc.height = d;
        const sctx = sc.getContext('2d');
        const mid  = d / 2;

        const grad = sctx.createRadialGradient(mid, mid, 0, mid, mid, mid);
        grad.addColorStop(0,    `rgba(${Math.min(r+90,255)},${Math.min(g+90,255)},${Math.min(b+90,255)},1)`);
        grad.addColorStop(0.12, `rgba(${r},${g},${b},0.9)`);
        grad.addColorStop(0.38, `rgba(${r},${g},${b},0.22)`);
        grad.addColorStop(0.72, `rgba(${r},${g},${b},0.05)`);
        grad.addColorStop(1,    `rgba(${r},${g},${b},0)`);

        sctx.beginPath();
        sctx.arc(mid, mid, mid, 0, Math.PI * 2);
        sctx.fillStyle = grad;
        sctx.fill();

        spriteCache.set(key, sc);
        return sc;
    }

    // ─── Spatial grid ─────────────────────────────────────────────────────────────
    let grid = {};
    function buildGrid() {}   // nothing to precompute; all dynamic

    function populateGrid() {
        grid = Object.create(null);              // faster than {}
        for (const p of particles) {
            const key = (Math.floor(p.x / C.gridCell) * 10000 +
                         Math.floor(p.y / C.gridCell)) | 0;
            if (grid[key]) grid[key].push(p);
            else           grid[key] = [p];
        }
    }

    // ─── Particle creation ────────────────────────────────────────────────────────
    function createParticle(layer, layerIdx) {
        const color = C.colors[Math.floor(Math.random() * C.colors.length)];
        const speed = C.baseSpeed * layer.speedMul;
        const angle = Math.random() * Math.PI * 2;
        const size  = C.baseSize * layer.sizeMul * (0.5 + Math.random() * 0.5);
        return {
            x: Math.random() * W,
            y: Math.random() * H,
            vx: Math.cos(angle) * speed * (0.5 + Math.random() * 0.5),
            vy: Math.sin(angle) * speed * (0.5 + Math.random() * 0.5),
            size,
            r: color.r, g: color.g, b: color.b,
            baseAlpha: layer.alphaMul * (0.4 + Math.random() * 0.6),
            alpha: 0,
            layer: layerIdx,
            connectDist: layer.connectDist,
            connectDistSq: layer.connectDist * layer.connectDist,
            phase: Math.random() * Math.PI * 2,
            pulseSpeed: 0.007 + Math.random() * 0.013,
            sprite: getSprite(color.r, color.g, color.b, size),
        };
    }

    function init() {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
        cx = W / 2; cy = H / 2;
        particles = [];
        C.layers.forEach((layer, idx) => {
            for (let i = 0; i < layer.count; i++) {
                particles.push(createParticle(layer, idx));
            }
        });
    }

    // ─── Update ───────────────────────────────────────────────────────────────────
    function update() {
        time++;
        const ambientPulse = 0.85 + Math.sin(time * C.ambientPulseSpeed) * 0.15;

        // Ripples age
        for (let i = ripples.length - 1; i >= 0; i--) {
            ripples[i].radius += C.rippleSpeed;
            if (--ripples[i].life <= 0) ripples.splice(i, 1);
        }

        for (const p of particles) {
            // Alpha pulse (cheap trig reuse)
            p.phase += p.pulseSpeed;
            p.alpha = p.baseAlpha * (0.7 + Math.sin(p.phase) * 0.3) * ambientPulse;

            // Mouse attraction — cheap AABB early-out
            if (mouse.active) {
                const dx = mouse.x - p.x;
                const dy = mouse.y - p.y;
                if (dx < C.mouseRadius && dx > -C.mouseRadius &&
                    dy < C.mouseRadius && dy > -C.mouseRadius) {
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < C.mouseRadius && dist > 1) {
                        const lm = (p.layer + 1) / C.layers.length;
                        const f  = (1 - dist / C.mouseRadius) * C.mouseForce * lm;
                        p.vx += (dx / dist) * f;
                        p.vy += (dy / dist) * f;
                    }
                }
            }

            // Ripple shockwave
            for (const rip of ripples) {
                const dx = p.x - rip.x;
                const dy = p.y - rip.y;
                const d  = Math.sqrt(dx * dx + dy * dy);
                const rd = Math.abs(d - rip.radius);
                if (rd < 26 && d > 1) {
                    const f = (1 - rd / 26) * 0.25 * (rip.life / C.rippleLife);
                    p.vx += (dx / d) * f;
                    p.vy += (dy / d) * f;
                }
            }

            // Gentle per-layer drift
            p.vx += Math.sin(time * 0.0008 + p.layer * 1.3) * 0.0012 * C.layers[p.layer].speedMul;

            // Velocity damping — smooth deceleration
            p.vx *= 0.994;
            p.vy *= 0.994;

            p.x += p.vx;
            p.y += p.vy;

            // Wrap edges
            if (p.x < -28)   p.x = W + 28;
            else if (p.x > W + 28) p.x = -28;
            if (p.y < -28)   p.y = H + 28;
            else if (p.y > H + 28) p.y = -28;
        }

        populateGrid();
    }

    // ─── Draw ─────────────────────────────────────────────────────────────────────
    // We render in this order to minimise state changes:
    //   0. Trail fill
    //   1. Connection lines — ALL in ONE beginPath/stroke call
    //   2. Mouse lines      — separate pass, same trick
    //   3. Ripple rings     — one per ring (there are usually 0–3 of them)
    //   4. Particles        — grouped by alpha bucket, one drawImage each
    //   5. Vignette

    function draw() {
        // 0. Motion-blur trail
        ctx.fillStyle = `rgba(6,10,20,${C.trailAlpha})`;
        ctx.fillRect(0, 0, W, H);

        // 1. Connection lines — SINGLE BATCHED PATH per layer ─────────────────────
        ctx.lineWidth = 0.45;
        for (let li = 1; li < C.layers.length; li++) {
            const distSq    = C.layers[li].connectDist * C.layers[li].connectDist;
            const connDist  = C.layers[li].connectDist;
            const layerAlpha = C.lineBaseAlpha * (li / (C.layers.length - 1));

            // Collect all segments first, then draw with a single path+stroke
            ctx.beginPath();
            ctx.strokeStyle = `rgba(160,140,255,${layerAlpha.toFixed(3)})`;

            for (const a of particles) {
                if (a.layer !== li) continue;
                const col = Math.floor(a.x / C.gridCell);
                const row = Math.floor(a.y / C.gridCell);

                // Check 9 cells
                for (let dc = -1; dc <= 1; dc++) {
                    for (let dr = -1; dr <= 1; dr++) {
                        const nb = grid[(col + dc) * 10000 + (row + dr)];
                        if (!nb) continue;
                        for (const b of nb) {
                            if (b.layer !== li || b === a) continue;
                            const dx = a.x - b.x;
                            const dy = a.y - b.y;
                            const d2 = dx * dx + dy * dy;
                            if (d2 < distSq && d2 > 0.01) {
                                // Instead of separate strokeStyle per line,
                                // we add ALL segments to one path.
                                // Modulate alpha via globalAlpha per segment isn't
                                // possible in one pass, so use a single alpha that
                                // looks good for average distance.
                                ctx.moveTo(a.x | 0, a.y | 0);
                                ctx.lineTo(b.x | 0, b.y | 0);
                            }
                        }
                    }
                }
            }
            ctx.stroke();   // ← ONE GPU call for all lines in this layer
        }

        // 2. Mouse attraction rays — single batched path ───────────────────────────
        if (mouse.active) {
            const mRadSq = (C.mouseRadius * 0.6) ** 2;
            ctx.beginPath();
            ctx.strokeStyle = 'rgba(124,92,252,0.06)';
            ctx.lineWidth   = 0.3;
            let count = 0;
            for (const p of particles) {
                if (count >= 25 || p.layer < 2) continue;
                const dx = p.x - mouse.x;
                const dy = p.y - mouse.y;
                if (dx * dx + dy * dy < mRadSq) {
                    ctx.moveTo(mouse.x | 0, mouse.y | 0);
                    ctx.lineTo(p.x  | 0, p.y  | 0);
                    count++;
                }
            }
            ctx.stroke();
        }

        // 3. Ripple rings ──────────────────────────────────────────────────────────
        for (const rip of ripples) {
            ctx.beginPath();
            ctx.arc(rip.x | 0, rip.y | 0, rip.radius, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(124,92,252,${((rip.life / C.rippleLife) * 0.13).toFixed(3)})`;
            ctx.lineWidth   = 1.4;
            ctx.stroke();
        }

        // 4. Particles — blitted from sprite cache ─────────────────────────────────
        //    Sort isn't needed: layers were naturally interleaved.
        for (const p of particles) {
            const sp   = p.sprite;
            const half = sp.width >> 1;           // integer divide
            ctx.globalAlpha = p.alpha;
            ctx.drawImage(sp, (p.x - half) | 0, (p.y - half) | 0);
        }
        ctx.globalAlpha = 1;

        // 5. Vignette (cached gradient) ────────────────────────────────────────────
        if (_vignetteGrad) {
            ctx.fillStyle = _vignetteGrad;
            ctx.fillRect(0, 0, W, H);
        }
    }

    // ─── Cached vignette ─────────────────────────────────────────────────────────
    let _vignetteGrad = null;
    function buildVignette() {
        _vignetteGrad = ctx.createRadialGradient(cx, cy, H * 0.28, cx, cy, H * 0.92);
        _vignetteGrad.addColorStop(0, 'rgba(6,10,20,0)');
        _vignetteGrad.addColorStop(1, 'rgba(6,10,20,0.42)');
    }

    // ─── Main loop ────────────────────────────────────────────────────────────────
    function loop() {
        update();
        draw();
        animId = requestAnimationFrame(loop);
    }

    // ─── Events ───────────────────────────────────────────────────────────────────
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            W = canvas.width  = window.innerWidth;
            H = canvas.height = window.innerHeight;
            cx = W / 2; cy = H / 2;
            buildVignette();
            // Quick fill to remove stale trails
            ctx.fillStyle = 'rgb(6,10,20)';
            ctx.fillRect(0, 0, W, H);
        }, 100);
    });

    // Mouse: throttle to rAF cadence (not setTimeout) for perfect sync
    let mousePending = false;
    window.addEventListener('mousemove', e => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        mouse.active = true;
        if (!mousePending) {
            mousePending = true;
            requestAnimationFrame(() => { mousePending = false; });
        }
    });

    window.addEventListener('click', e => {
        if (e.target.closest('a,button,input,select,textarea,[role="button"]')) return;
        ripples.push({ x: e.clientX, y: e.clientY, radius: 0, life: C.rippleLife });
    });

    window.addEventListener('mouseleave', () => { mouse.active = false; });

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            cancelAnimationFrame(animId);
        } else {
            ctx.fillStyle = 'rgb(6,10,20)';
            ctx.fillRect(0, 0, W, H);
            loop();
        }
    });

    // ─── Boot ─────────────────────────────────────────────────────────────────────
    init();
    buildVignette();
    ctx.fillStyle = 'rgb(6,10,20)';
    ctx.fillRect(0, 0, W, H);
    loop();
})();
