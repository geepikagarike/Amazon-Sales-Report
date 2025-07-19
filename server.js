const express = require('express');
const app = express();
const PORT = 3000;

// Middleware
app.use(express.json());

// Root route
app.get('/', (req, res) => {
  res.send('✅ Server is running fine!');
});

// Start the server
app.listen(PORT, () => {
  console.log(`🚀 Server is running at http://localhost:${PORT}`);
});
