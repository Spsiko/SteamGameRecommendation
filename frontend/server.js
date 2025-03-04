const express = require('express'),
    expressLayouts = require('express-ejs-layouts'),
    bodyParser = require('body-parser')

require('dotenv').config()
const path = require('path')
const cors = require('cors')
const app = express()

const port = process.env.PORT || 80;

// Middleware
app.use(express.json());
app.use(cors());

//used for forms
app.use(bodyParser.urlencoded({ extended: true }))
app.set('view engine', 'ejs')
app.use(expressLayouts)

// Serve static files from 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Import and use routes (once we have them)
//app.use(require('./app/routes'))

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
})

module.exports = app