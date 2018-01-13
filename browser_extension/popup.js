function contentScriptMantra() {
    chrome.tabs.executeScript({
      file: 'mantra.js'
    }); 
  }
function contentScriptClassic() {
    chrome.tabs.executeScript({
      file: 'classic.js'
    }); 
  }
// load jquery to use in content scripts
chrome.tabs.executeScript({
  file: "jquery.min.js"
});
console.log("ICDQCMAS loaded jquery");
document.getElementById("button-mantra").addEventListener("click", contentScriptMantra);
document.getElementById("button-classic").addEventListener("click", contentScriptClassic);