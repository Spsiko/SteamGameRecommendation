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

}
