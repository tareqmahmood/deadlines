
// Global state
let conferences = [];
let allDeadlines = [];
let allAreas = [];
let selectedAreas = new Set();

// Theme handling
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.textContent = savedTheme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
        toggleBtn.onclick = () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            toggleBtn.textContent = next === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
        };
    }
}

// Data fetching
const DB_KEY = 'deadline_db_cache';

async function loadData() {
    // 1. Try cache
    const cached = localStorage.getItem(DB_KEY);
    let cachedData = null;
    if (cached) {
        try {
            cachedData = JSON.parse(cached);
            processData(cachedData);
            renderCurrentPage(true); // Render immediately with cached data
        } catch (e) {
            console.error("Cache parse error", e);
        }
    }

    // 2. Fetch network
    try {
        const response = await fetch('db.json');
        const data = await response.json();
        
        // Check if data changed
        if (!cachedData || JSON.stringify(data) !== cached) {
            localStorage.setItem(DB_KEY, JSON.stringify(data));
            processData(data);
            renderCurrentPage(false); // Re-render with new data
        }
        return true;
    } catch (e) {
        console.error("Network fetch error", e);
        return false;
    }
}

function processData(data) {
    conferences = data.conferences;
    allAreas = data.areas;
    processDeadlines();
}

function renderCurrentPage(isCached) {
    // Helper to render the correct page based on URL
    if (window.location.pathname.endsWith('calendar.html')) {
        renderCalendarPage();
    } else if (window.location.pathname.endsWith('conference.html')) {
        renderConferencePage();
    } else {
        // Default to deadlines page
        renderDeadlinesPage(!isCached); // Only read URL params if not a re-render from cache update? 
        // Actually, we always want to respect URL params.
        // But renderDeadlinesPage(true) means "read URL params".
        // If we are updating from network, we still want to respect URL params.
        renderDeadlinesPage(true);
    }
}

function processDeadlines() {
    allDeadlines = [];
    conferences.forEach(conf => {
        if (conf.deadlines) {
            conf.deadlines.forEach(d => {
                // Parse date
                // Format: "2026-01-29 12:00:00" and timezone "UTC+0"
                // Convert to ISO string for Date constructor
                let tz = d.timezone.replace('UTC', '');
                if (tz === '' || tz === '+0') tz = 'Z';
                // Handle +8 or -5
                if (tz !== 'Z' && !tz.includes(':')) {
                    // if it's just +8, make it +08:00
                    const sign = tz.startsWith('-') ? '-' : '+';
                    let num = tz.replace(sign, '');
                    if (num.length === 1) num = '0' + num;
                    tz = `${sign}${num}:00`;
                }
                
                const paperDateStr = `${d.paper_deadline.replace(' ', 'T')}${tz}`;
                const paperDate = new Date(paperDateStr);
                
                const abstractDateStr = d.abstract_deadline ? `${d.abstract_deadline.replace(' ', 'T')}${tz}` : null;
                const abstractDate = abstractDateStr ? new Date(abstractDateStr) : null;

                allDeadlines.push({
                    confTitle: conf.title,
                    confYear: conf.year,
                    confId: conf.id,
                    venue: conf.venue,
                    areas: conf.areas,
                    cfpLink: conf.cfp_link,
                    season: d.season,
                    paperDeadline: paperDate,
                    abstractDeadline: abstractDate,
                    timezone: d.timezone,
                    raw: d
                });
            });
        }
    });
    
    // Sort by paper deadline
    allDeadlines.sort((a, b) => a.paperDeadline - b.paperDeadline);
}

// Time formatting
function getTimeRemaining(endtime) {
    const total = Date.parse(endtime) - Date.parse(new Date());
    const seconds = Math.floor((total / 1000) % 60);
    const minutes = Math.floor((total / 1000 / 60) % 60);
    const hours = Math.floor((total / (1000 * 60 * 60)) % 24);
    const days = Math.floor(total / (1000 * 60 * 60 * 24));
    return {
        total,
        days,
        hours,
        minutes,
        seconds
    };
}

function formatLocalTime(date) {
    return date.toLocaleString(undefined, {
        weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', 
        hour: '2-digit', minute: '2-digit', timeZoneName: 'short'
    });
}

// Google Calendar Link
function createCalendarUrl(title, start, details, location) {
    const formatDate = (date) => date.toISOString().replace(/-|:|\.\d\d\d/g, "");
    // Add 1 hour duration
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    
    return `https://www.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${formatDate(start)}/${formatDate(end)}&details=${encodeURIComponent(details)}&location=${encodeURIComponent(location)}&sf=true&output=xml`;
}

// Page specific renderers
function renderAreaFilter() {
    const container = document.getElementById('area-filter');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (allAreas.length === 0) return;

    // Add "All" option? Or just deselect all means all?
    // Let's stick to toggling tags. If none selected, show all.
    
    allAreas.forEach(area => {
        const tag = document.createElement('div');
        tag.className = 'filter-tag';
        tag.textContent = area;
        if (selectedAreas.has(area.toLowerCase())) {
            tag.classList.add('active');
        }
        
        tag.onclick = () => {
            const lowerArea = area.toLowerCase();
            if (selectedAreas.has(lowerArea)) {
                selectedAreas.delete(lowerArea);
                tag.classList.remove('active');
            } else {
                selectedAreas.add(lowerArea);
                tag.classList.add('active');
            }
            
            // Update URL
            const url = new URL(window.location);
            if (selectedAreas.size > 0) {
                url.searchParams.set('areas', Array.from(selectedAreas).join(','));
            } else {
                url.searchParams.delete('areas');
            }
            window.history.pushState({}, '', url);
            
            renderDeadlinesPage(false); // false to skip re-reading URL params
        };
        
        container.appendChild(tag);
    });
}

function renderDeadlinesPage(readUrl = true) {
    const container = document.getElementById('deadlines-container');
    container.innerHTML = '';
    
    // Filter by area if needed
    if (readUrl) {
        const urlParams = new URLSearchParams(window.location.search);
        const areasParam = urlParams.get('areas');
        selectedAreas.clear();
        if (areasParam) {
            areasParam.split(',').forEach(a => selectedAreas.add(a.trim().toLowerCase()));
        }
    }
    
    // Render filter UI
    renderAreaFilter();

    let displayDeadlines = allDeadlines;
    
    if (selectedAreas.size > 0) {
        displayDeadlines = allDeadlines.filter(d => 
            d.areas.some(area => selectedAreas.has(area.toLowerCase()))
        );
    }
    
    // Filter past deadlines? Prompt says "next 10 deadlines".
    const now = new Date();
    displayDeadlines = displayDeadlines.filter(d => d.paperDeadline > now);
    
    // Take top 10
    displayDeadlines = displayDeadlines.slice(0, 10);
    
    if (displayDeadlines.length === 0) {
        container.innerHTML = '<p>No upcoming deadlines found.</p>';
        return;
    }

    displayDeadlines.forEach((d, index) => {
        const card = document.createElement('div');
        card.className = 'deadline-card';
        
        const seasonStr = d.season ? ` (${d.season})` : '';
        const title = `${d.confTitle} ${d.confYear}${seasonStr}`;
        
        const tags = d.areas.map(a => `<span class="tag">${a}</span>`).join('');
        
        const calUrl = createCalendarUrl(
            `${title} Paper Deadline`, 
            d.paperDeadline, 
            `CFP: ${d.cfpLink}`, 
            d.venue
        );

        card.innerHTML = `
            <div class="deadline-left">
                <div class="deadline-header">
                    <a href="conference.html?id=${d.confId}" class="conf-title">${title}</a>
                    <div class="conf-tags">${tags}</div>
                </div>
                <div class="venue">${d.venue}</div>
                <div class="dates">
                    ${d.abstractDeadline ? `
                    <div class="date-item">
                        <span class="date-label">Abstract:</span>
                        <span class="date-value">${formatLocalTime(d.abstractDeadline)}</span>
                    </div>` : ''}
                    <div class="date-item">
                        <span class="date-label">Paper:</span>
                        <span class="date-value">${formatLocalTime(d.paperDeadline)}</span>
                    </div>
                </div>
            </div>
            <div class="deadline-right">
                <div class="timer" id="timer-${index}">Loading...</div>
                <div class="card-links">
                    <a href="${d.cfpLink}" target="_blank" title="Call for Papers">🔗 CFP</a>
                    <a href="${calUrl}" target="_blank" title="Add to Calendar">📅 Add to Cal</a>
                </div>
            </div>
        `;
        container.appendChild(card);
        
        // Start timer
        const timerEl = card.querySelector(`#timer-${index}`);
        const updateTimer = () => {
            const t = getTimeRemaining(d.paperDeadline);
            if (t.total <= 0) {
                timerEl.textContent = "Deadline Passed";
            } else {
                timerEl.textContent = `${t.days}d ${t.hours}h ${t.minutes}m ${t.seconds}s`;
            }
        };
        updateTimer();
        setInterval(updateTimer, 1000);
    });
}

function renderCalendarPage() {
    const now = new Date();
    let currentYear = now.getFullYear();
    
    const container = document.getElementById('calendar-grid-container');
    const yearLabel = document.getElementById('year-label');
    
    function render() {
        yearLabel.textContent = currentYear;
        container.innerHTML = '';
        
        // Render 12 months
        for (let month = 0; month < 12; month++) {
            const monthContainer = document.createElement('div');
            monthContainer.className = 'month-container';
            
            const monthTitle = document.createElement('div');
            monthTitle.className = 'month-title';
            monthTitle.textContent = new Date(currentYear, month).toLocaleString('default', { month: 'long' });
            monthContainer.appendChild(monthTitle);
            
            const grid = document.createElement('div');
            grid.className = 'calendar-grid';
            
            // Headers
            ['S', 'M', 'T', 'W', 'T', 'F', 'S'].forEach(day => {
                const el = document.createElement('div');
                el.className = 'calendar-day-header';
                el.textContent = day;
                grid.appendChild(el);
            });
            
            const firstDay = new Date(currentYear, month, 1);
            const lastDay = new Date(currentYear, month + 1, 0);
            
            // Empty slots
            for (let i = 0; i < firstDay.getDay(); i++) {
                const el = document.createElement('div');
                el.className = 'calendar-day empty';
                grid.appendChild(el);
            }
            
            // Days
            for (let i = 1; i <= lastDay.getDate(); i++) {
                const dayEl = document.createElement('div');
                dayEl.className = 'calendar-day';
                dayEl.textContent = i;
                
                const currentDate = new Date(currentYear, month, i);
                
                // Check for today
                const today = new Date();
                if (currentDate.getDate() === today.getDate() && 
                    currentDate.getMonth() === today.getMonth() && 
                    currentDate.getFullYear() === today.getFullYear()) {
                    dayEl.classList.add('today');
                }

                const nextDate = new Date(currentYear, month, i + 1);
                
                const events = [];
                
                // Find events
                allDeadlines.forEach(d => {
                    if (d.paperDeadline >= currentDate && d.paperDeadline < nextDate) {
                        events.push({ type: 'paper', title: `${d.confTitle} Paper`, id: d.confId });
                    }
                    if (d.abstractDeadline && d.abstractDeadline >= currentDate && d.abstractDeadline < nextDate) {
                        events.push({ type: 'abstract', title: `${d.confTitle} Abs`, id: d.confId });
                    }
                });
                
                conferences.forEach(c => {
                    const start = new Date(c.start);
                    const end = new Date(c.end);
                    const cDate = new Date(currentDate);
                    cDate.setHours(0,0,0,0);
                    const sDate = new Date(start);
                    sDate.setHours(0,0,0,0);
                    const eDate = new Date(end);
                    eDate.setHours(0,0,0,0);
                    
                    if (cDate >= sDate && cDate <= eDate) {
                        events.push({ type: 'conference', title: `${c.title}`, id: c.id });
                    }
                });
                
                if (events.length > 0) {
                    dayEl.classList.add('has-event');
                    
                    const barsContainer = document.createElement('div');
                    barsContainer.className = 'event-bars';
                    
                    const tooltip = document.createElement('div');
                    tooltip.className = 'event-tooltip';
                    
                    events.forEach(ev => {
                        const bar = document.createElement('div');
                        bar.className = `event-bar ${ev.type}`;
                        barsContainer.appendChild(bar);
                        
                        const line = document.createElement('div');
                        line.textContent = ev.title;
                        tooltip.appendChild(line);
                    });
                    
                    dayEl.appendChild(barsContainer);
                    dayEl.appendChild(tooltip);
                    dayEl.onclick = () => window.location.href = `conference.html?id=${events[0].id}`;
                }
                
                grid.appendChild(dayEl);
            }
            
            monthContainer.appendChild(grid);
            container.appendChild(monthContainer);
        }
    }
    
    document.getElementById('prev-year').onclick = () => {
        currentYear--;
        render();
    };
    
    document.getElementById('next-year').onclick = () => {
        currentYear++;
        render();
    };
    
    render();
}

function renderConferencePage() {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');
    
    if (!id) {
        document.getElementById('conference-container').innerHTML = '<p>Conference not found.</p>';
        return;
    }
    
    const conf = conferences.find(c => c.id === id);
    if (!conf) {
        document.getElementById('conference-container').innerHTML = '<p>Conference not found.</p>';
        return;
    }
    
    document.title = `${conf.title} ${conf.year} - Deadlines`;
    
    const container = document.getElementById('conference-container');
    
    // Map link
    const mapLink = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(conf.venue)}`;
    
    let deadlinesHtml = '';
    if (conf.deadlines) {
        conf.deadlines.forEach((d, idx) => {
            // Re-parse dates locally as we might not have processed them if we didn't run processDeadlines fully or want specific logic
            // But we can find the processed deadline object in allDeadlines
            const processed = allDeadlines.find(ad => ad.raw === d && ad.confId === conf.id);
            
            if (!processed) return;
            
            const paperCal = createCalendarUrl(`${conf.title} Paper`, processed.paperDeadline, `CFP: ${conf.cfp_link}`, conf.venue);
            const absCal = processed.abstractDeadline ? createCalendarUrl(`${conf.title} Abstract`, processed.abstractDeadline, `CFP: ${conf.cfp_link}`, conf.venue) : '#';
            
            const isPassed = processed.paperDeadline < new Date();
            
            deadlinesHtml += `
                <div class="deadline-item ${isPassed ? 'passed' : ''}">
                    <h3>${d.season ? d.season : 'Main'} Deadline</h3>
                    <div class="timer" id="timer-${idx}"></div>
                    
                    <p><strong>Paper Deadline:</strong> ${formatLocalTime(processed.paperDeadline)} 
                       <a href="${paperCal}" target="_blank">[Add to Cal]</a>
                    </p>
                    
                    ${processed.abstractDeadline ? `
                    <p><strong>Abstract Deadline:</strong> ${formatLocalTime(processed.abstractDeadline)}
                       <a href="${absCal}" target="_blank">[Add to Cal]</a>
                    </p>` : ''}
                    
                    ${d.author_notification ? `
                    <p><strong>Notification:</strong> ${d.author_notification}</p>` : ''}
                </div>
            `;
            
            // Timer logic needs to be attached after insertion
            setTimeout(() => {
                const timerEl = document.getElementById(`timer-${idx}`);
                if (timerEl) {
                    const update = () => {
                        const t = getTimeRemaining(processed.paperDeadline);
                        if (t.total <= 0) timerEl.textContent = "Deadline Passed";
                        else timerEl.textContent = `${t.days}d ${t.hours}h ${t.minutes}m ${t.seconds}s`;
                    };
                    update();
                    setInterval(update, 1000);
                }
            }, 0);
        });
    }
    
    container.innerHTML = `
        <div class="detail-header">
            <h1>${conf.title} ${conf.year}</h1>
            <div class="venue">
                📍 <a href="${mapLink}" target="_blank">${conf.venue}</a>
            </div>
            <div class="dates">
                📅 ${conf.start} to ${conf.end}
            </div>
            <div style="margin-top: 1rem;">
                <a href="${conf.cfp_link}" target="_blank" class="tag">Website / CFP</a>
            </div>
        </div>
        
        <div class="detail-deadlines">
            ${deadlinesHtml}
        </div>
    `;
}
