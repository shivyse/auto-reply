/**
 * TubePulse US - YouTube Automation Dashboard Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  let appIntel = null;
  let availableVoices = [];
  let selectedVoiceId = "caleb_us";
  let channelState = null;

  // Init App
  initNavigation();
  fetchUSIntel();
  fetchVoices();
  fetchQueue();
  fetchAutopilot();
  fetchCuriosityVault();
  setupEventListeners();
  startUSTimeTicker();
});

// ----------------- NAVIGATION -----------------

function initNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  const tabContents = document.querySelectorAll(".tab-content");

  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const targetTabId = item.getAttribute("data-tab");

      navItems.forEach(btn => btn.classList.remove("active"));
      tabContents.forEach(tab => tab.classList.remove("active"));

      item.classList.add("active");
      const activeTab = document.getElementById(targetTabId);
      if (activeTab) activeTab.classList.add("active");
    });
  });

  const btnQuickNav = document.getElementById("btnQuickNavAutomate");
  if (btnQuickNav) {
    btnQuickNav.addEventListener("click", () => {
      document.querySelector('[data-tab="tab-automate"]').click();
    });
  }
}

// ----------------- API CALLS -----------------

async function fetchUSIntel() {
  try {
    const res = await fetch("/api/us-intel");
    const data = await res.json();
    appIntel = data;

    updateUSTimes(data.us_times);
    updateOptimalSlot(data.optimal_slot);
    renderNiches(data.niches);
    renderTrends(data.trends);
  } catch (err) {
    console.error("Error fetching US intelligence:", err);
  }
}

async function fetchVoices() {
  try {
    const res = await fetch("/api/voices");
    const data = await res.json();
    availableVoices = data.voices || [];
    renderVoices(availableVoices);
  } catch (err) {
    console.error("Error fetching voices:", err);
  }
}

// ----------------- AUTOPILOT & CURIOSITY API -----------------

async function fetchAutopilot() {
  try {
    const res = await fetch("/api/autopilot/status");
    const state = await res.json();
    renderAutopilotState(state);
  } catch (err) {
    console.error("Error fetching autopilot status:", err);
  }
}

function renderAutopilotState(state) {
  if (!state) return;

  const currentDay = state.current_day || 1;
  const maxShortsDays = state.shorts_only_duration_days || 5;
  const subs = state.audience_subscribers || 0;
  const targetSubs = state.switch_threshold_subs || 500;
  const phase = state.current_phase || "SHORTS_BLITZ";

  // Phase Badge
  const badge = document.getElementById("currentPhaseBadge");
  if (badge) {
    if (phase === "SHORTS_BLITZ") {
      badge.className = "badge badge-accent";
      badge.innerHTML = `<i class="fa-solid fa-bolt"></i> Phase 1: Shorts-Only Blitz (Day ${currentDay})`;
    } else {
      badge.className = "badge badge-success";
      badge.innerHTML = `<i class="fa-solid fa-rocket"></i> Phase 2: Hybrid Scale (Shorts + Long-Form)`;
    }
  }

  // Phase Boxes Styling
  const boxShorts = document.getElementById("phaseBoxShorts");
  const boxHybrid = document.getElementById("phaseBoxHybrid");
  const tagShorts = document.getElementById("tagShortsStatus");
  const tagHybrid = document.getElementById("tagHybridStatus");

  if (boxShorts && boxHybrid) {
    if (phase === "SHORTS_BLITZ") {
      boxShorts.className = "phase-box phase-active";
      boxHybrid.className = "phase-box phase-locked";
      if (tagShorts) tagShorts.innerHTML = "● ACTIVE STRATEGY";
      if (tagHybrid) tagHybrid.innerHTML = `LOCKED (Unlocks Day ${maxShortsDays + 1} or 500 Subs)`;
    } else {
      boxShorts.className = "phase-box";
      boxHybrid.className = "phase-box phase-active";
      if (tagShorts) tagShorts.innerHTML = "COMPLETED (Now Running in Hybrid)";
      if (tagHybrid) tagHybrid.innerHTML = "● ACTIVE STRATEGY (Shorts + Long-Form)";
    }
  }

  // Day & Subscriber Progress
  const dispDay = document.getElementById("dispCurrentDay");
  if (dispDay) dispDay.textContent = `Day ${currentDay} of ${maxShortsDays}`;

  const dayFill = document.getElementById("dayProgressFill");
  if (dayFill) {
    const dayPct = Math.min(100, Math.round((currentDay / maxShortsDays) * 100));
    dayFill.style.width = `${dayPct}%`;
  }

  const dispSubs = document.getElementById("dispSubscribers");
  if (dispSubs) dispSubs.textContent = `${subs.toLocaleString()} / ${targetSubs.toLocaleString()} Subs`;

  const subFill = document.getElementById("subProgressFill");
  if (subFill) {
    const subPct = Math.min(100, Math.round((subs / targetSubs) * 100));
    subFill.style.width = `${subPct}%`;
  }

  const dispViews = document.getElementById("dispCumulativeViews");
  if (dispViews) dispViews.textContent = (state.audience_views || 0).toLocaleString();

  const dispSched = document.getElementById("dispScheduleMode");
  if (dispSched) {
    dispSched.textContent = phase === "SHORTS_BLITZ" ? "2 Shorts / Day" : "1 Short + 1 Long / Day";
  }

  // Activity Log
  const logBox = document.getElementById("autopilotLogBox");
  if (logBox && state.activity_log) {
    logBox.innerHTML = "";
    state.activity_log.slice(0, 10).forEach(entry => {
      const row = document.createElement("div");
      row.className = "log-entry";
      row.innerHTML = `
        <div class="log-time">${entry.timestamp}</div>
        <div class="log-msg">${entry.message}</div>
      `;
      logBox.appendChild(row);
    });
  }
}

async function fetchCuriosityVault() {
  try {
    const res = await fetch("/api/curiosity/topics");
    const data = await res.json();
    renderCuriosityTopics(data.topics || []);
  } catch (err) {
    console.error("Error fetching curiosity vault:", err);
  }
}

function renderCuriosityTopics(topics) {
  const container = document.getElementById("curiosityVaultContainer");
  if (!container || !topics) return;

  container.innerHTML = "";
  topics.forEach(t => {
    const card = document.createElement("div");
    card.className = "curiosity-card";
    card.innerHTML = `
      <div>
        <div class="cur-card-top">
          <span class="tag-pill">${t.category}</span>
          <span class="cur-score-badge"><i class="fa-solid fa-fire"></i> ${t.curiosity_score}% Intrigue</span>
        </div>
        <div class="cur-title">${t.topic}</div>
        <div class="cur-anomaly"><strong>The Anomaly:</strong> ${t.anomaly}</div>
        <div class="cur-hook-box">"${t.open_loop_hook}"</div>
      </div>
      <div style="display: flex; gap: 8px;">
        <button class="btn btn-sm btn-primary btn-auto-curiosity" data-id="${t.id}" data-format="shorts" style="flex:1;">
          <i class="fa-solid fa-play"></i> Auto-Create Short
        </button>
        <button class="btn btn-sm btn-secondary btn-auto-curiosity" data-id="${t.id}" data-format="long_form" title="Create 10m Long-Form Video">
          <i class="fa-solid fa-film"></i> Long-Form
        </button>
      </div>
    `;

    card.querySelectorAll(".btn-auto-curiosity").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        const id = e.currentTarget.getAttribute("data-id");
        const format = e.currentTarget.getAttribute("data-format");
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Producing...`;
        showToast(`Autonomous production started for: "${t.topic}" (${format})...`, "info");

        try {
          const res = await fetch("/api/curiosity/generate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({topic_id: id, format})
          });
          const d = await res.json();
          showToast(`🎉 Video Ready! Added to US Publishing Queue.`, "success");
          fetchQueue();
          fetchAutopilot();

          // Switch to 1-Click automate tab and show player
          document.querySelector('[data-tab="tab-automate"]').click();
          const player = document.getElementById("renderedVideoPlayer");
          if (player && d.video) {
            player.src = d.video.url;
            player.poster = d.thumbnail_url;
            player.load();
          }
        } catch (err) {
          showToast("Error generating curiosity video: " + err.message, "error");
        } finally {
          btn.disabled = false;
          btn.innerHTML = format === "shorts" ? `<i class="fa-solid fa-play"></i> Auto-Create Short` : `<i class="fa-solid fa-film"></i> Long-Form`;
        }
      });
    });

    container.appendChild(card);
  });
}


// ----------------- RENDER FUNCTIONS -----------------

function updateUSTimes(times) {
  if (!times) return;
  const estEl = document.getElementById("estTime");
  const cstEl = document.getElementById("cstTime");
  const mstEl = document.getElementById("mstTime");
  const pstEl = document.getElementById("pstTime");

  if (estEl) estEl.textContent = times.EST;
  if (cstEl) cstEl.textContent = times.CST;
  if (mstEl) mstEl.textContent = times.MST;
  if (pstEl) pstEl.textContent = times.PST;
}

function updateOptimalSlot(slot) {
  if (!slot) return;
  const slotEl = document.getElementById("nextSlotText");
  if (slotEl) slotEl.textContent = slot.recommended_slot;
}

function startUSTimeTicker() {
  setInterval(async () => {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      updateUSTimes(data.us_times);
      updateOptimalSlot(data.next_upload_window);
    } catch (e) {}
  }, 30000);
}

function renderNiches(niches) {
  const container = document.getElementById("nichesContainer");
  if (!container || !niches) return;

  container.innerHTML = "";
  Object.values(niches).forEach(n => {
    const card = document.createElement("div");
    card.className = "niche-card";
    card.innerHTML = `
      <div class="niche-top">
        <span class="badge badge-accent">${n.badge}</span>
        <div class="niche-rpm">$${n.avg_rpm.toFixed(2)} RPM</div>
      </div>
      <div class="niche-title"><i class="fa-solid ${n.icon}" style="color: ${n.color}"></i> ${n.name}</div>
      <div class="niche-states"><i class="fa-solid fa-location-dot"></i> Top US States: ${n.top_us_states.join(", ")}</div>
      <div class="mt-2 text-xs text-muted"><strong>Style:</strong> ${n.retention_style}</div>
      <button class="btn btn-sm btn-outline mt-3 btn-use-niche" data-niche="${n.id}">
        <i class="fa-solid fa-arrow-right"></i> Target This US Niche
      </button>
    `;

    card.querySelector(".btn-use-niche").addEventListener("click", () => {
      document.getElementById("autoNiche").value = n.id;
      document.querySelector('[data-tab="tab-automate"]').click();
      showToast(`Selected US Niche: ${n.name}`, "info");
    });

    container.appendChild(card);
  });
}

function renderTrends(trends) {
  const tbody = document.getElementById("trendsTableBody");
  if (!tbody || !trends) return;

  tbody.innerHTML = "";
  trends.forEach(t => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${t.topic}</strong></td>
      <td><span class="tag-pill">${t.niche}</span></td>
      <td>${t.search_volume}</td>
      <td><span class="badge ${t.competition === 'Low' ? 'badge-success' : 'badge-accent'}">${t.competition}</span></td>
      <td class="text-emerald font-bold">${t.projected_rpm}</td>
      <td><span class="text-cyan font-bold">${t.trend_score}/100</span></td>
      <td>
        <button class="btn btn-sm btn-primary btn-trend-auto" data-topic="${encodeURIComponent(t.topic)}" data-niche="${t.niche}">
          <i class="fa-solid fa-bolt"></i> Automate
        </button>
      </td>
    `;

    tr.querySelector(".btn-trend-auto").addEventListener("click", (e) => {
      const topic = decodeURIComponent(e.currentTarget.getAttribute("data-topic"));
      const niche = e.currentTarget.getAttribute("data-niche");

      document.getElementById("autoTopic").value = topic;
      document.getElementById("autoNiche").value = niche;
      document.querySelector('[data-tab="tab-automate"]').click();
      showToast(`Loaded US Trend: "${topic}"`, "info");
    });

    tbody.appendChild(tr);
  });
}

function renderVoices(voices) {
  const container = document.getElementById("voicesContainer");
  if (!container || !voices) return;

  container.innerHTML = "";
  voices.forEach(v => {
    const card = document.createElement("div");
    card.className = `voice-card ${v.id === selectedVoiceId ? 'selected' : ''}`;
    card.setAttribute("data-voice", v.id);
    card.innerHTML = `
      <div>
        <div class="voice-name"><i class="fa-solid fa-user-astronaut"></i> ${v.name}</div>
        <div class="voice-meta">${v.accent} • ${v.tone}</div>
      </div>
      <span class="badge badge-accent">${v.best_for}</span>
    `;

    card.addEventListener("click", () => {
      document.querySelectorAll(".voice-card").forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      selectedVoiceId = v.id;
      showToast(`Active American Voice: ${v.name}`, "info");
    });

    container.appendChild(card);
  });
}

function renderQueue(queue) {
  const tbody = document.getElementById("queueTableBody");
  if (!tbody) return;

  tbody.innerHTML = "";
  if (queue.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 24px;">No videos queued. Click "Batch 3 US Shorts" or use 1-Click Automation.</td></tr>`;
    return;
  }

  queue.forEach(item => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <strong>${item.title || item.topic}</strong>
        <div class="text-xs text-muted">${item.duration} • ID: ${item.id}</div>
      </td>
      <td><span class="tag-pill">${item.niche}</span></td>
      <td>${item.format}</td>
      <td><span class="text-cyan">${item.scheduled_slot_us}</span></td>
      <td class="text-emerald font-bold">${item.projected_rpm}</td>
      <td><span class="badge ${item.status === 'Published' ? 'badge-success' : 'badge-accent'}">${item.status}</span></td>
      <td>
        <div style="display: flex; gap: 6px;">
          ${item.video_url ? `<a href="${item.video_url}" target="_blank" class="btn btn-sm btn-secondary" title="View Video"><i class="fa-solid fa-play"></i></a>` : ''}
          ${item.status !== 'Published' ? `<button class="btn btn-sm btn-primary btn-publish-item" data-id="${item.id}" data-title="${encodeURIComponent(item.title)}"><i class="fa-solid fa-cloud-arrow-up"></i> Publish</button>` : '<span class="text-xs text-emerald"><i class="fa-solid fa-check"></i> Live</span>'}
        </div>
      </td>
    `;

    const pubBtn = tr.querySelector(".btn-publish-item");
    if (pubBtn) {
      pubBtn.addEventListener("click", async (e) => {
        const id = e.currentTarget.getAttribute("data-id");
        const title = decodeURIComponent(e.currentTarget.getAttribute("data-title"));
        pubBtn.disabled = true;
        pubBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;

        try {
          const res = await fetch("/api/queue/publish", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({id, title})
          });
          const resData = await res.json();
          showToast(`Published to YouTube! Video ID: ${resData.upload_result.video_id}`, "success");
          fetchQueue();
        } catch (err) {
          showToast("Publish error: " + err.message, "error");
        }
      });
    }

    tbody.appendChild(tr);
  });
}

// ----------------- EVENT LISTENERS -----------------

function setupEventListeners() {
  // 1-Click Automate Form
  const autoForm = document.getElementById("quickAutomateForm");
  if (autoForm) {
    autoForm.addEventListener("submit", handleQuickAutomate);
  }

  // Random Trend Button
  const btnRandomTrend = document.getElementById("btnRandomTrend");
  if (btnRandomTrend) {
    btnRandomTrend.addEventListener("click", () => {
      if (appIntel && appIntel.trends && appIntel.trends.length > 0) {
        const randomTrend = appIntel.trends[Math.floor(Math.random() * appIntel.trends.length)];
        document.getElementById("autoTopic").value = randomTrend.topic;
        document.getElementById("autoNiche").value = randomTrend.niche;
        showToast(`Loaded Trend: "${randomTrend.topic}"`, "info");
      }
    });
  }

  // Refresh Intel button
  const btnRefreshIntel = document.getElementById("btnRefreshIntel");
  if (btnRefreshIntel) {
    btnRefreshIntel.addEventListener("click", async () => {
      await fetchUSIntel();
      showToast("US Audience Intelligence refreshed!", "info");
    });
  }

  // Copy SEO
  const btnCopySEO = document.getElementById("btnCopySEO");
  if (btnCopySEO) {
    btnCopySEO.addEventListener("click", () => {
      const desc = document.getElementById("dispDesc").value;
      navigator.clipboard.writeText(desc);
      showToast("YouTube Description copied to clipboard!", "success");
    });
  }

  // Script Generator Form (Tab 3)
  const scriptForm = document.getElementById("scriptGenForm");
  if (scriptForm) {
    scriptForm.addEventListener("submit", handleGenerateScript);
  }

  // Thumbnail Generator Form (Tab 5)
  const thumbForm = document.getElementById("thumbGenForm");
  if (thumbForm) {
    thumbForm.addEventListener("submit", handleGenerateThumbnail);
  }

  // Voice Audition (Tab 4)
  const btnTestVoice = document.getElementById("btnTestVoice");
  if (btnTestVoice) {
    btnTestVoice.addEventListener("click", speakAuditionPhrase);
  }

  const btnStopVoice = document.getElementById("btnStopVoice");
  if (btnStopVoice) {
    btnStopVoice.addEventListener("click", () => {
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    });
  }

  const btnSpeakScript = document.getElementById("btnSpeakScript");
  if (btnSpeakScript) {
    btnSpeakScript.addEventListener("click", () => {
      const text = document.getElementById("scriptOutputText").value;
      speakWithUSVoice(text);
    });
  }

  // Revenue Calculator Sliders (Tab 7)
  const viewsRange = document.getElementById("viewsRange");
  const usPctRange = document.getElementById("usPctRange");
  const calcNiche = document.getElementById("calcNiche");

  if (viewsRange && usPctRange && calcNiche) {
    const updateRevCalc = async () => {
      const views = parseInt(viewsRange.value);
      const usPct = parseInt(usPctRange.value);
      const niche = calcNiche.value;

      document.getElementById("viewsSliderVal").textContent = views.toLocaleString();
      document.getElementById("usPctVal").textContent = `${usPct}%`;

      try {
        const res = await fetch("/api/calculate-revenue", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({views, niche, us_share: usPct / 100.0})
        });
        const d = await res.json();
        document.getElementById("calcTotal").textContent = d.total_projected_usd;
        document.getElementById("calcAdsense").textContent = d.adsense_revenue;
        document.getElementById("calcSponsor").textContent = d.sponsorship_revenue;
        document.getElementById("calcAffiliate").textContent = d.affiliate_revenue;
        document.getElementById("dispBlendedRPM").textContent = d.blended_rpm;
      } catch (e) {}
    };

    viewsRange.addEventListener("input", updateRevCalc);
    usPctRange.addEventListener("input", updateRevCalc);
    calcNiche.addEventListener("change", updateRevCalc);
  }

  // Batch Generation (Tab 6)
  const btnBatchGen3 = document.getElementById("btnBatchGen3");
  if (btnBatchGen3) {
    btnBatchGen3.addEventListener("click", async () => {
      btnBatchGen3.disabled = true;
      btnBatchGen3.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating 3 US Shorts...`;
      showToast("Generating batch of 3 US Shorts...", "info");

      try {
        const res = await fetch("/api/batch-generate", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({niche: "finance", count: 3})
        });
        const d = await res.json();
        showToast(`Batch completed: ${d.batch_count} videos created and scheduled!`, "success");
        fetchQueue();
      } catch (err) {
        showToast("Batch error: " + err.message, "error");
      } finally {
        btnBatchGen3.disabled = false;
        btnBatchGen3.innerHTML = `<i class="fa-solid fa-cubes"></i> Batch 3 US Shorts`;
      }
    });
  }

  const btnRefreshQueue = document.getElementById("btnRefreshQueue");
  if (btnRefreshQueue) {
    btnRefreshQueue.addEventListener("click", () => {
      fetchQueue();
      showToast("Publishing queue refreshed!", "info");
    });
  }

  // Autopilot Buttons
  const btnAdvanceDay = document.getElementById("btnAdvanceDay");
  if (btnAdvanceDay) {
    btnAdvanceDay.addEventListener("click", async () => {
      btnAdvanceDay.disabled = true;
      btnAdvanceDay.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Advancing Day & Producing...`;
      showToast("Advancing channel to next day...", "info");

      try {
        const res = await fetch("/api/autopilot/advance-day", {
          method: "POST"
        });
        const d = await res.json();
        renderAutopilotState(d.state);
        fetchQueue();
        showToast(`Advanced to Day ${d.day}! Phase: ${d.phase}. New audience: ${d.audience.subscribers} subs.`, "success");
      } catch (err) {
        showToast("Error advancing day: " + err.message, "error");
      } finally {
        btnAdvanceDay.disabled = false;
        btnAdvanceDay.innerHTML = `<i class="fa-solid fa-forward-step"></i> Advance to Next Day (+1 Day)`;
      }
    });
  }

  const btnRunDailyCycle = document.getElementById("btnRunDailyCycle");
  if (btnRunDailyCycle) {
    btnRunDailyCycle.addEventListener("click", async () => {
      btnRunDailyCycle.disabled = true;
      btnRunDailyCycle.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Executing Daily Run...`;
      showToast("Executing autonomous creation cycle...", "info");

      try {
        const res = await fetch("/api/autopilot/run-cycle", {
          method: "POST"
        });
        const d = await res.json();
        renderAutopilotState(d.state);
        fetchQueue();
        showToast(`Cycle finished! Produced ${d.items_created.length} new videos for ${d.phase}.`, "success");
      } catch (err) {
        showToast("Error executing cycle: " + err.message, "error");
      } finally {
        btnRunDailyCycle.disabled = false;
        btnRunDailyCycle.innerHTML = `<i class="fa-solid fa-play"></i> Run Today's Production`;
      }
    });
  }

  const btnTogglePhase = document.getElementById("btnTogglePhase");
  if (btnTogglePhase) {
    btnTogglePhase.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/autopilot/switch-phase", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({})
        });
        const d = await res.json();
        renderAutopilotState(d.state);
        showToast(`Phase toggled to: ${d.new_phase}`, "info");
      } catch (err) {
        showToast("Error toggling phase: " + err.message, "error");
      }
    });
  }

  const btnRefreshActivity = document.getElementById("btnRefreshActivity");
  if (btnRefreshActivity) {
    btnRefreshActivity.addEventListener("click", () => {
      fetchAutopilot();
      showToast("Activity log refreshed!", "info");
    });
  }
}

// ----------------- PIPELINE HANDLERS -----------------

async function handleQuickAutomate(e) {
  e.preventDefault();

  const topic = document.getElementById("autoTopic").value.trim();
  const niche = document.getElementById("autoNiche").value;
  const format = document.getElementById("autoFormat").value;
  const badge = document.getElementById("autoBadge").value.trim();

  const btnRun = document.getElementById("btnRunAutomate");
  const progressBox = document.getElementById("pipelineProgress");

  btnRun.disabled = true;
  btnRun.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Autonomously Producing Video...`;
  progressBox.style.display = "block";

  // Reset steps
  updateStep("step1", "active", "1. US Hook & Scriptwriting (In Progress...)");
  updateStep("step2", "waiting", "2. High-CTR 1280x720 Thumbnail");
  updateStep("step3", "waiting", "3. FFmpeg Kinetic Video & Audio Rendering");
  updateStep("step4", "waiting", "4. US SEO Metadata & FTC Compliance");
  updateStep("step5", "waiting", "5. Packaging Deliverable Bundle");

  // Step 1 mock progression
  setTimeout(() => updateStep("step1", "done", "1. US Hook & Scriptwriting ✓"), 1000);
  setTimeout(() => updateStep("step2", "active", "2. Rendering High-CTR 1280x720 Thumbnail..."), 1200);
  setTimeout(() => updateStep("step2", "done", "2. High-CTR Thumbnail Generated ✓"), 2200);
  setTimeout(() => updateStep("step3", "active", "3. FFmpeg Compiling 1080p Video + Audio..."), 2400);

  try {
    const res = await fetch("/api/quick-automate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        topic,
        niche,
        format,
        custom_badge: badge || undefined
      })
    });

    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    const data = await res.json();

    updateStep("step3", "done", `3. FFmpeg Video Rendered (${data.video.size_mb} MB) ✓`);
    updateStep("step4", "done", "4. US SEO Metadata & FTC Compliance ✓");
    updateStep("step5", "done", "5. ZIP Deliverable Bundle Packaged ✓");

    // Update Media Player
    const player = document.getElementById("renderedVideoPlayer");
    player.src = data.video.url;
    player.poster = data.thumbnail.url;
    player.load();

    // Update Action Buttons
    const btnDownVid = document.getElementById("btnDownloadVideo");
    btnDownVid.href = data.video.url;

    const btnDownThumb = document.getElementById("btnDownloadThumb");
    btnDownThumb.href = data.thumbnail.url;

    const btnDownZip = document.getElementById("btnDownloadBundle");
    if (data.bundle_zip_url) {
      btnDownZip.href = data.bundle_zip_url;
      btnDownZip.style.display = "inline-flex";
    }

    // Update Metrics
    document.getElementById("metricRetention").textContent = `${data.script.analysis.retention_score}%`;
    document.getElementById("metricRPM").textContent = `$${data.seo.avg_us_rpm.toFixed(2)}`;
    document.getElementById("metricCTR").textContent = data.thumbnail.ctr_analysis.predicted_ctr;

    // Update SEO Card
    document.getElementById("dispTitle").textContent = data.seo.selected_title;
    document.getElementById("dispDesc").value = data.seo.description;

    const tagsBox = document.getElementById("dispTags");
    tagsBox.innerHTML = "";
    (data.seo.tags || []).slice(0, 10).forEach(t => {
      const sp = document.createElement("span");
      sp.className = "tag-pill";
      sp.textContent = t;
      tagsBox.appendChild(sp);
    });

    // Refresh Queue Table
    fetchQueue();

    showToast("🎉 Full YouTube Automation Package Completed!", "success");

  } catch (err) {
    console.error("Pipeline failure:", err);
    showToast("Error generating video: " + err.message, "error");
  } finally {
    btnRun.disabled = false;
    btnRun.innerHTML = `<i class="fa-solid fa-rocket"></i> Generate Complete YouTube Automation`;
  }
}

function updateStep(stepId, state, text) {
  const el = document.getElementById(stepId);
  if (!el) return;

  el.className = `step-item ${state}`;
  if (state === "done") {
    el.innerHTML = `<i class="fa-solid fa-check text-emerald"></i> ${text}`;
  } else if (state === "active") {
    el.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin text-amber"></i> ${text}`;
  } else {
    el.innerHTML = `<i class="fa-regular fa-circle"></i> ${text}`;
  }
}

async function handleGenerateScript(e) {
  e.preventDefault();
  const topic = document.getElementById("scriptTopicInput").value.trim();
  const niche = document.getElementById("scriptNicheSelect").value;
  const format = document.getElementById("scriptFormatSelect").value;
  const hook_style = document.getElementById("scriptHookSelect").value;

  const btn = document.getElementById("btnGenScript");
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Writing...`;

  try {
    const res = await fetch("/api/generate-script", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({topic, niche, format, hook_style})
    });
    const d = await res.json();

    document.getElementById("diagScore").textContent = `${d.analysis.retention_score}%`;
    document.getElementById("diagWords").textContent = d.analysis.word_count;
    document.getElementById("diagDuration").textContent = d.analysis.duration_str;
    document.getElementById("diagGrade").textContent = `Grade ${d.analysis.fk_grade}`;
    document.getElementById("scriptOutputText").value = d.full_text;

    showToast("US Retention Script Generated!", "success");
  } catch (err) {
    showToast("Script generation error: " + err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-pen-to-square"></i> Generate Retention Script`;
  }
}

async function handleGenerateThumbnail(e) {
  e.preventDefault();
  const topic = document.getElementById("thumbHeadline").value.trim();
  const niche = document.getElementById("thumbNiche").value;
  const badge = document.getElementById("thumbBadgeInput").value.trim();

  const btn = document.getElementById("btnGenThumbOnly");
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Rendering...`;

  try {
    const res = await fetch("/api/generate-thumbnail", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({topic, niche, custom_badge: badge || undefined})
    });
    const d = await res.json();

    const img = document.getElementById("thumbPreviewImg");
    img.src = `${d.thumbnail_url}?t=${Date.now()}`;

    // Update Feed Simulator
    const simImg = document.getElementById("simThumb");
    if (simImg) simImg.src = img.src;

    const simTitle = document.getElementById("simTitle");
    if (simTitle) simTitle.textContent = `${topic} (2026 EXPOSED)`;

    document.getElementById("ctrValText").textContent = `${d.ctr_analysis.predicted_ctr} CTR`;

    showToast("High-CTR Thumbnail Rendered!", "success");
  } catch (err) {
    showToast("Thumbnail render error: " + err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-wand-magic"></i> Render Thumbnail`;
  }
}

// ----------------- AMERICAN VOICE SPEECH SYNTHESIS -----------------

function speakAuditionPhrase() {
  const phrase = document.getElementById("auditionPhrase").value;
  speakWithUSVoice(phrase);
}

function speakWithUSVoice(text) {
  if (!('speechSynthesis' in window)) {
    showToast("Web Speech API not supported in your browser.", "error");
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);

  // Set American voice configuration
  const voiceConfig = availableVoices.find(v => v.id === selectedVoiceId) || {
    rate: 1.05,
    pitch: 1.0
  };

  utterance.rate = voiceConfig.rate || 1.05;
  utterance.pitch = voiceConfig.pitch || 1.0;
  utterance.lang = "en-US";

  // Pick suitable en-US voice from system
  const systemVoices = window.speechSynthesis.getVoices();
  const usVoice = systemVoices.find(v => v.lang.startsWith("en-US") || v.lang.startsWith("en_US")) || systemVoices.find(v => v.lang.startsWith("en"));

  if (usVoice) utterance.voice = usVoice;

  window.speechSynthesis.speak(utterance);
  showToast(`Speaking with American voice: ${voiceConfig.name || "US English"}`, "info");
}

// ----------------- TOAST UTILITIES -----------------

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const icon = type === "success" ? "fa-circle-check" : (type === "error" ? "fa-circle-exclamation" : "fa-circle-info");
  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}
