//This file is based in part on AI code generation

async function searchSteamGame() {
    const gameName = document.getElementById("gameInput").value;
    const response = await fetch(`/serverRequest?type=search&game=${encodeURIComponent(gameName)}`);
    
    if (!response.ok) {
        console.error("Error fetching from server");
        return;
    }

    const games = await response.json();
    console.log("Search Results: ", games)
    const resultsList = document.getElementById("results");
    resultsList.innerHTML = ""

    games.forEach(game => {
        const li = document.createElement("li")
        li.innerHTML = `<img src="${game.icon}" alt="ico"> ${game.name}`
        li.classList.add("list-group-item", "list-group-item-action")
        li.onclick = () => displayDetails(game.appid);
        resultsList.appendChild(li);
    });
}

async function displayDetails(appid) {
    const response = await fetch(`/serverRequest?type=game&appid=${encodeURIComponent(appid)}`);
    
    if (!response.ok) {
        console.error("Error fetching from server");
        return;
    }

    const info = await response.json();
    console.log("Game Info", info)

    document.getElementById("icon").src = `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/header.jpg`;
    data = info[appid].data

    document.getElementById("description").innerHTML = `<p>${data.short_description}</p>`
    document.getElementById("gameTitle").innerHTML = `<p><b>${data.name}</b></p>`
}

async function getRecommendation() {
    //I want to get the user's profile URL and then send it to the server
    //To get back their library and then get a recommendation
    const profileURL = document.getElementById("profileInput").value;
    console.log("Profile URL: ", profileURL);
    const urlParts = profileURL.split('/');
    const vanityURL = urlParts[urlParts.length - 2]; // Extract the vanity URL from the profile URL
    console.log("Vanity URL: ", vanityURL);

    // Resolve the vanity URL to a Steam ID
    const resolveResponse = await fetch(`/resolveVanityURL?vanityurl=${encodeURIComponent(vanityURL)}`);
    
    if (!resolveResponse.ok) {
        console.error("Error resolving vanity URL");
        return;
    }

    const resolveData = await resolveResponse.json();
    steamID = resolveData.response.steamid;
    // const steamID = "76561198163428013";
    console.log("Steam ID: ", steamID);

    // Fetch the user's Steam library using the resolved Steam ID
    const libraryResponse = await fetch(`/getSteamLibrary?steamid=${encodeURIComponent(steamID)}`);
    
    if (!libraryResponse.ok) {
        console.error("Error fetching from server");
        return;
    }

    const library = await libraryResponse.json();
    console.log("Steam Library: ", library);
    // Process the library data to get recommendations
}
