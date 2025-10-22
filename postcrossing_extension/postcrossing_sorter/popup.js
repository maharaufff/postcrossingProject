document.getElementById("sortBtn").addEventListener("click", async () => {
    const status = document.getElementById("status");
    status.textContent = "Sorting tabs...";

    try {
        await chrome.runtime.sendMessage({ action: "sortTabs" });
        status.textContent = "Tabs sorted successfully!";
    } catch (err) {
        status.textContent = "Error: " + err;
    }
});
