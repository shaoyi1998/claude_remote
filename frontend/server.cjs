const express = require('express')
const path = require('path')
const app = express()
const port = 3000

// 静态文件
app.use(express.static(path.join(__dirname, 'dist')))

// SPA 路由 - 所有路由返回 index.html
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'))
})

app.listen(port, '0.0.0.0', () => {
  console.log(`Server running at http://0.0.0.0:${port}`)
})
