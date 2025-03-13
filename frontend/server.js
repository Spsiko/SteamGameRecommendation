//This file is based in part on AI code generation
const express = require('express')
const path = require('path')

const app = express()
const port = 3000

app.use(express.static(path.join(__dirname, 'public')))

app.get('/serverRequest', async (req, res) => {
    const type = req.query.type
    let url = ''

    //Determining which type of information is needed from Steam
    if(type === 'search') {
        const gameName = req.query.game
        url = `https://steamcommunity.com/actions/SearchApps/${encodeURIComponent(gameName)}`
    } else {
        const appid = req.query.appid
        url = `https://store.steampowered.com/api/appdetails?appids=${encodeURIComponent(appid)}`
    }

    try {
        const response = await fetch(url)
        if (!response.ok) {
            throw new Error(`Steam API error: ${response.status}`)
        }

        const data = await response.json()
        res.json(data)
    } catch (error) {
        console.error("Error fetching from Steam:", error)
        res.status(500).json({ error: "Failed to fetch from Steam" })
    }
})

app.listen(port, () => {
    console.log(`Server is running on port ${port}`)
})