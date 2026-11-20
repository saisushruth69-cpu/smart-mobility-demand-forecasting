const $ = (s) => document.querySelector(s);

const hourSelect = document.querySelector('select[name="hour"]');
for (let h = 0; h < 24; h++) {
  const option = document.createElement('option');
  option.value = h;
  option.textContent = `${String(h).padStart(2,'0')}:00`;
  if (h === 17) option.selected = true;
  hourSelect.appendChild(option);
}

function formPayload(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  return {
    year: Number(data.year), season: Number(data.season), month: Number(data.month), hour: Number(data.hour),
    holiday: Number(data.holiday), weekday: Number(data.weekday), workingday: Number(data.workingday), weathersit: Number(data.weathersit),
    temp: Number(data.temp), atemp: Number(data.atemp), hum: Number(data.hum), windspeed: Number(data.windspeed)
  };
}

$('#forecastForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const status = $('#formStatus');
  status.textContent = 'Calculating…';
  $('#resultBadge').textContent = 'RUNNING';
  try {
    const response = await fetch('/predict', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(formPayload(event.target))});
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Prediction failed');
    $('#predictedDemand').textContent = Number(result.predicted_demand).toLocaleString();
    $('#profileValue').textContent = result.demand_profile;
    $('#recommendationValue').textContent = result.recommendation;
    $('#resultProfile').textContent = result.demand_profile === 'High Demand' ? 'The selected conditions point to a busy period. Consider increasing availability.' : result.demand_profile === 'Low Demand' ? 'The selected conditions point to a quieter period.' : 'The selected conditions sit in the normal operating range.';
    $('#resultBadge').textContent = 'COMPLETE';
    $('#heroDemand').textContent = Number(result.predicted_demand).toLocaleString();
    $('#heroProfile').textContent = result.demand_profile;
    status.textContent = 'Forecast updated just now.';
  } catch (error) {
    $('#resultBadge').textContent = 'ERROR';
    status.textContent = error.message;
  }
});

function maxValue(items, key) { return Math.max(...items.map(x => Number(x[key]) || 0), 1); }
function renderHourChart(items) {
  const el = $('#hourChart'); const max = maxValue(items,'cnt'); el.innerHTML='';
  items.forEach(item => { const bar=document.createElement('div'); bar.className='bar'; bar.style.height=`${Math.max(4,(Number(item.cnt)/max)*100)}%`; bar.title=`${item.hr}:00 — ${Math.round(item.cnt)} bikes`; bar.innerHTML=`<span class="bar-label">${item.hr}</span>`; el.appendChild(bar); });
}
function renderMiniBars(el, items, labelFn) {
  const max=maxValue(items,'cnt'); el.innerHTML='';
  items.forEach(item=>{const row=document.createElement('div');row.className='mini-row';row.innerHTML=`<span>${labelFn(item)}</span><span class="mini-track"><span class="mini-fill" style="width:${(Number(item.cnt)/max)*100}%"></span></span><span class="mini-value">${Math.round(item.cnt)}</span>`;el.appendChild(row);});
}

async function loadAnalytics(){
  try{
    const response=await fetch('/api/analytics');
    const data=await response.json();
    renderHourChart(data.hourly_demand || []);
    const weekdays=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    renderMiniBars($('#weekdayChart'), data.weekday_demand || [], x=>weekdays[x.weekday] ?? x.weekday);
    const weather=['Clear','Mist','Rain','Storm'];
    renderMiniBars($('#weatherChart'), data.weather_demand || [], x=>weather[(x.weathersit||1)-1] ?? x.weathersit);
  }catch(error){
    $('#hourChart').innerHTML='<p style="color:#8b9087;font-size:12px">Analytics unavailable.</p>';
  }
}

const themeBtn = $('#themeBtn');
function applyTheme(theme){
  document.body.classList.toggle('theme-dark', theme === 'dark');
  themeBtn.textContent = theme === 'dark' ? '☀' : '◐';
  themeBtn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
  localStorage.setItem('rideflow-theme', theme);
}
applyTheme(localStorage.getItem('rideflow-theme') || 'light');
themeBtn.addEventListener('click',()=>{
  applyTheme(document.body.classList.contains('theme-dark') ? 'light' : 'dark');
});
loadAnalytics();
