import React, { useState, useEffect, useRef } from 'react';
import * as Plotly from 'plotly.js-dist-min';

// change to backend url when get flask running
const API_BASE_URL = 'http://localhost:5000/api';
const USE_SAMPLE_DATA = true;  // flip to false when backend ready


// sample data for now
const FALLBACK_DATA = {
  'google.ca': { privacy: 606, security: 714, lastScan: 'Oct 18, 2025' },
  'facebook.com': { privacy: 450, security: 680, lastScan: 'Oct 15, 2025' },
  'china-scooter.ru': { privacy: 920, security: 880, lastScan: 'Oct 20, 2025' },
  'netbk.co.jp': { privacy: 270, security: 460, lastScan: 'Oct 19, 2025' }
};

const FALLBACK_SITES = [
  { name: 'china-scooter.ru', privacy: 92, security: 88 },
  { name: 'google.ca', privacy: 62, security: 78 },
  { name: 'facebook.com', privacy: 45, security: 68 },
  { name: 'netbk.co.jp', privacy: 27, security: 46 }
];



function PlotlyChart({ data, layout, config }) {
  const plotRef = useRef(null);
  
  useEffect(() => {
    if (plotRef.current) {
      Plotly.newPlot(plotRef.current, data, layout, config);
    }
    
    return () => {
      if (plotRef.current) {
        Plotly.purge(plotRef.current);
      }
    };
  }, [data, layout, config]);
  
  return <div ref={plotRef} className="w-full" />;
}


export default function PrivacyDashboard() {
  const [selectedsite, setselectedsite] = useState('google.ca');
  const [inputValue, setInputValue] = useState('google.ca');
  const [siteData, setSiteData] = useState({});
  const [allSites, setAllSites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const currentdata = siteData[selectedsite] || { privacy: 0, security: 0, lastScan: 'N/A' };


  // load sample data if backend aint ready
  const loadSampleData = () => {
    console.log('using sample data - backend not connected');
    setSiteData(FALLBACK_DATA);
    setAllSites(FALLBACK_SITES);
  };


  // grab all sites when page loads
  useEffect(() => {     
    const fetchAllSites = async () => {
      if (USE_SAMPLE_DATA) {     

        loadSampleData();
        return;
      }

      setLoading(true);
      try {
        // endpoint: get /api/sites
        // returns: { [domain]: { privacy, security, lastScan } }
        const response = await fetch(`${API_BASE_URL}/sites`);
        if (!response.ok) throw new Error(`http error status: ${response.status}`);
        
        const data = await response.json();
        console.log('got data from backend:', data);
        
        setSiteData(data);
        
        // converting to array for the charts
        const sitesArr = Object.keys(data).map(siteName => ({
          name: siteName,    

          privacy: data[siteName].privacy || 0,
          security: data[siteName].security || 50
        }));
        setAllSites(sitesArr);
        
      } catch (err) {
            
        console.error('couldnt fetch from backend:', err);
        setError('backend not responding. using sample data instead');
        loadSampleData();
           
      } finally {  
        setLoading(false);
      }
    };
    
    fetchAllSites();                       

  }, []);



  // handles when user hits analyze button
  const handleAnalyze = async () => {
    if (!inputValue.trim()) {
      alert('need to enter a website first'); 
      return; 
    }

    // if still using sample data just switch sites
    if (USE_SAMPLE_DATA) {
      if (siteData[inputValue]) {
        setselectedsite(inputValue);
      } else {
        alert('site not in sample data. try: google.ca, facebook.com, china-scooter.ru, netbk.co.jp');
      }
      return; 
    }
    
    setLoading(true);      
    setError(null);
    
    try {
      // POST /api/analyze/:site
      const response = await fetch(`${API_BASE_URL}/analyze/${inputValue}`);
      
      if (!response.ok) {
        throw new Error('site not found or analysis failed');
      }
      
      const data = await response.json();
      console.log('analysis result:', data);
      
      // adding new site data
      setSiteData(prev => ({
        ...prev,
        [inputValue]: {
          privacy: data.privacy || 0,
          security: data.security || 50,
          lastScan: data.lastScan || 'recently',
          trackers: data.totalTrackers || 0
        }
      }));
      
      // update charts if its a new site
      if (!allSites.find(s => s.name === inputValue)) {
        setAllSites(prev => [...prev, {
          name: inputValue,
          privacy: data.privacy || 0,
          security: data.security || 50     
        }]);
      }
      
      setselectedsite(inputValue);
      
    } catch (err) {    
      console.error('analyze failed:', err);
      setError(`couldnt analyze ${inputValue}. ${err.message}`);
      alert(`error: ${err.message}`);
    } finally {        
      setLoading(false);
    }
  };


  const handleExChange = (e) => {
    const val = e.target.value;
    if (val) {
      setInputValue(val);
      setselectedsite(val);
    }
  };


  // figuring out risk level from avg of privacy + security
  const getRisk = (priv, sec) => {
    const avg = (priv + sec) / 2;
    
    if (avg >= 700) return { level: 'Good', color: '#4CAF50', angle: -45 };
    if (avg >= 500) return { level: 'Moderate', color: '#FF9800', angle: 0 };
    return { level: 'High Risk', color: '#f44336', angle: 45 };
  };   
  
  const risk = getRisk(currentdata.privacy, currentdata.security);
  


  // bar chart setup
  const barData = [
    {
      x: allSites.map(s => s.name),
      y: allSites.map(s => s.privacy),
      name: 'Privacy Score',
      type: 'bar',
      marker: { color: '#4CAF50' }   
    }, 
    {
      x: allSites.map(s => s.name),
      y: allSites.map(s => s.security),
      name: 'Security Score',
      type: 'bar',
      marker: { color: '#2196F3' }         
    }
  ];
  
  const barLayout = {
    title: 'Privacy & Security Comparison',
    xaxis: { title: 'Platform' },
    yaxis: { title: 'Score', range: [0, 100] },        
    barmode: 'group',
    height: 320,
    margin: { t: 40, b: 80, l: 50, r: 20 }
  };
  

  // scatter plot for privacy vs security
  const scatterData = [{
    x: allSites.map(s => s.privacy),
    y: allSites.map(s => s.security),
    mode: 'markers+text',
    type: 'scatter',
    text: allSites.map(s => s.name),
    textposition: 'top center',
    marker: {
      size: 12,
      color: allSites.map(s => {
        if (s.name === selectedsite) return '#FF9800';  // highlight selected
        if (s.privacy >= 70) return '#4CAF50';  // good
        if (s.privacy >= 40) return '#FF9800';  // mid
        return '#f44336';  // bad
      })
    }
  }];
  
  const scatterLayout = {
    title: 'Privacy vs Security',
    xaxis: { title: 'Privacy Score', range: [0, 100] },
    yaxis: { title: 'Security Score', range: [0, 100] },
    height: 280,
    margin: { t: 40, b: 50, l: 50, r: 20 }
  };


  
  // risk meter
  const gaugeData = [{
    type: 'indicator',
    mode: 'gauge+number',
    value: (currentdata.privacy + currentdata.security) / 2,
    title: { text: 'Overall Risk Score' },
    gauge: {
      axis: { range: [0, 100] },
      bar: { color: risk.color },
      steps: [
        { range: [0, 40], color: '#ffebee' },
        { range: [40, 70], color: '#fff8e1' },
        { range: [70, 100], color: '#e8f5e9' }
      ],
      threshold: {
        line: { color: 'black', width: 2 },
        thickness: 0.75,
        value: (currentdata.privacy + currentdata.security) / 2
      }
    }
  }];
  
  const gaugeLayout = {
    height: 250,
    margin: { t: 20, b: 20, l: 20, r: 20 }
  };
  
  const plotCfg = { responsive: true, displayModeBar: false };


  //Best and Worst sites
  const best = allSites.reduce((max, site) => site.privacy > max.privacy ? site : max, allSites[0] || { name: 'N/A', privacy: 0 });
  const worst = allSites.reduce((min, site) => site.privacy < min.privacy ? site : min, allSites[0] || { name: 'N/A', privacy: 0 });



  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">     
      
      <header className="bg-white border-b-4 border-emerald-500 py-6 px-8 shadow-md">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <img src="/SSM Logo.png" alt="SSM Logo" className="h-20 w-20 object-contain" />       
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Privacy Rank Comparison Dashboard</h1>
            <p className="text-gray-600 text-sm mt-1">Smart Social Monitor — Informatica</p>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        
        {USE_SAMPLE_DATA && (   
          <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6 rounded">
            <p className="font-bold"> demo mode</p>
            <p className="text-sm">using sample data rn. backend not hooked up yet</p>
          </div>
        )}

        {loading && (
          <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-6 rounded">
            <p className="font-bold">loading...</p>
            <p className="text-sm">fetching from backend</p>
          </div>
        )}
        
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded">
            <p className="font-bold">error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}
        
        
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex flex-col lg:flex-row gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-600 mb-2">
                enter website or platform
              </label>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                placeholder="e.g., google.ca, facebook.com"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-600 mb-2">
                quick examples
              </label>
              <select
                onChange={handleExChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">— choose example —</option>
                <option value="google.ca">google.ca</option>
                <option value="china-scooter.ru">china-scooter.ru</option>
                <option value="netbk.co.jp">netbk.co.jp</option>
                <option value="facebook.com">facebook.com</option>
              </select>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => alert('compare feature coming soon')}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                compare
              </button>
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className={`px-6 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {loading ? 'analyzing...' : 'analyze'}
              </button>
            </div>
          </div>
        </div>



        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="text-sm font-semibold text-gray-500 mb-2">your site</div>
            <div className="text-2xl font-bold text-gray-900 mb-1">{selectedsite}</div>
            <div className="text-sm text-gray-500">last scanned: {currentdata.lastScan}</div>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="text-sm font-semibold text-gray-500 mb-2">privacy rank</div>
            <div className={`text-4xl font-bold ${currentdata.privacy >= 700 ? 'text-green-500' : currentdata.privacy >= 500 ? 'text-orange-500' : 'text-red-500'}`}>
              {currentdata.privacy}
            </div>
            <div className="text-sm text-gray-500">lower = better privacy</div>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="text-sm font-semibold text-gray-500 mb-2">security rank</div>
            <div className={`text-4xl font-bold ${currentdata.security >= 700 ? 'text-green-500' : currentdata.security >= 500 ? 'text-orange-500' : 'text-red-500'}`}>
              {currentdata.security}
            </div>
            <div className="text-sm text-gray-500">higher = better security</div>
          </div>
        </div>


        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm p-6">
            <PlotlyChart
              data={barData}
              layout={barLayout}
              config={plotCfg}
            />
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-bold mb-2">risk meter</h3>
            <PlotlyChart
              data={gaugeData}
              layout={gaugeLayout}
              config={plotCfg}
            />
            <div className="text-center text-sm text-gray-600 mt-2">
              classification: <span className="font-bold" style={{ color: risk.color }}>{risk.level}</span>
            </div>
          </div>
        </div>


        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <PlotlyChart
            data={scatterData}
            layout={scatterLayout}
            config={plotCfg}
          />
        </div>


        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-gradient-to-r from-green-500 to-green-400 rounded-xl shadow-sm p-6 text-white">
            <div className="text-sm opacity-90 font-semibold mb-1">best privacy site</div>
            <div className="text-2xl font-bold mb-2">{best.name}</div>
            <div className="text-lg">privacy score: {best.privacy}</div>
          </div>
          
          <div className="bg-gradient-to-r from-red-500 to-red-400 rounded-xl shadow-sm p-6 text-white">
            <div className="text-sm opacity-90 font-semibold mb-1">worst privacy site</div>
            <div className="text-2xl font-bold mb-2">{worst.name}</div>
            <div className="text-lg">privacy score: {worst.privacy}</div>
          </div>
        </div>

        
        <footer className="text-center text-gray-500 text-sm py-6">
          © 2025 informatica — smart social monitor • react + plotly
        </footer>
      </div>
    </div>
  );
}