browser.browserAction.onClicked.addListener(async () => {
  try {
    console.log("Icon clicked!");

    // Get all open tabs
    const tabs = await browser.tabs.query({});
    console.log("All tabs:", tabs.map(t => t.url));

    // Filter Postcrossing postcard tabs
    const postcrossingTabs = tabs.filter(tab =>
      tab.url && tab.url.includes("http://127.0.0.1:5000/postcards/")

    );

    if (postcrossingTabs.length === 0) {
      console.log("No Postcrossing tabs open.");
      return;
    }

    // Sort by numeric postcard code
    postcrossingTabs.sort((a, b) => {
      const codeA = parseInt(a.url.split("-")[1]);
      const codeB = parseInt(b.url.split("-")[1]);
      return codeA - codeB;
    });

    // Move tabs in sorted order
    for (let i = 0; i < postcrossingTabs.length; i++) {
      await browser.tabs.move(postcrossingTabs[i].id, { index: i });
    }

    console.log("✅ Tabs sorted successfully!");

    // Show notification
    browser.notifications.create({
      "type": "basic",
      "iconUrl": "postcard-32.png",
      "title": "Postcrossing Tabs Sorted",
      "message": `Successfully sorted ${postcrossingTabs.length} Postcrossing tabs!`
    });

  } catch (e) {
    console.error("Error:", e);
  }
});
