//This file is based in part on AI code generation

//The appid of the game currently selected from the search
let selectedID = ""

//Keyword search of steam, find individual games
async function searchSteamGame() {
    const gameName = document.getElementById("gameInput").value;
    const response = await fetch(`/serverRequest?type=search&game=${encodeURIComponent(gameName)}`);
    
    if (!response.ok) {
        console.error("Error fetching from server");
        return;
    }

    const games = await response.json();
    console.log("Search Results: ", games)
    const searchResults = document.getElementById("searchResults");
    searchResults.innerHTML = ""

    games.forEach(game => {
        selectedID = game.appid
        const li = document.createElement("li")
        li.innerHTML = `<img src="${game.icon}" alt="ico"> ${game.name}`
        li.classList.add("list-group-item", "list-group-item-action")
        li.onclick = () => displayDetails(game.appid);
        searchResults.appendChild(li);
    });
}

//Get a description and an image for the selected game
async function displayDetails(appid) {
    const response = await fetch(`/serverRequest?type=game&appid=${encodeURIComponent(appid)}`);
    
    if (!response.ok) {
        console.error("Error fetching from server");
        return;
    }

    const info = await response.json();
    console.log("Game Info", info)

    if(info[appid].data === undefined ) {
        console.log("Error: game information not found")
        return
    }

    document.getElementById("icon").src = `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/header.jpg`;
    data = info[appid].data

    document.getElementById("description").innerHTML = `<p>${data.short_description}</p>`
    document.getElementById("gameTitle").innerHTML = `<p><b>${data.name}</b></p>`
}

//Sends the selected game to be used as model input
async function recommendSingle(appid) {
    getModelOutput({response: {game_count: 1, games: [{"appid":appid,"playtime_deck_forever":0,
        "playtime_disconnected":0,"playtime_forever":0,"playtime_linux_forever":0,
        "playtime_mac_forever":0,"playtime_windows_forever":0,"rtime_last_played":0}]}})
}

//Get the user's profile URL and then send it to the server
//Then get their library and  obtain a recommendation
async function getRecommendation() {
    profileURL = document.getElementById("profileInput").value;
    console.log("Profile URL: ", profileURL);

    //We want to check if the last character is a back slash and if so get rid of it
    if (profileURL[profileURL.length - 1] === '/') {
        profileURL = profileURL.slice(0, -1);
    }

    const urlParts = profileURL.split('/');
    const vanityURL = urlParts[urlParts.length - 1]; // Extract the vanity URL from the profile URL
    console.log("Vanity URL: ", vanityURL);

    // Resolve the vanity URL to a Steam ID
    if (!isNaN(vanityURL)) {  // check if vanityURL is a number
        steamID = vanityURL;
    } else{
        const resolveResponse = await fetch(`/resolveVanityURL?vanityurl=${encodeURIComponent(vanityURL)}`);
        
        if (!resolveResponse.ok) {
            console.error("Error resolving vanity URL");
            return;
        }

        const resolveData = await resolveResponse.json();
        steamID = resolveData.response.steamid;
    }

    console.log("Steam ID: ", steamID);

    // Fetch the user's Steam library using the resolved Steam ID
    const libraryResponse = await fetch(`/getSteamLibrary?steamid=${encodeURIComponent(steamID)}`);
    
    if (!libraryResponse.ok) {
        console.error("Error fetching from server");
        return;
    }

    const library = await libraryResponse.json();
    console.log("Steam Library: ", library);
    getModelOutput(library)
}

//Sending one or more games to the model for predictions
async function getModelOutput(library) {
    console.log("Sending library to Flask:", library);

    // Extract list of AppIDs from library
    const userGames = library.response.games.map(game => game.appid);

    try {
        const recommendationResponse = await fetch('/getRecommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                games: userGames
            })
        });

        if (!recommendationResponse.ok) {
            console.error("Error fetching recommendations");
            return;
        }

        const responseJson = await recommendationResponse.json();
        console.log("Recommendations: ", responseJson);

        const recommendedAppIDs = responseJson.recommended_games;

        const gamesList = document.getElementById("gamesList");
        gamesList.innerHTML = "";

        recommendedAppIDs.forEach(appid => {
            const li = document.createElement("li");
            li.classList.add("list-group-item", "list-group-item-action");
            li.textContent = "AppID: " + appid;
            gamesList.appendChild(li);
        });

    } catch (error) {
        console.error("Error sending data to Flask:", error);
    }
}

