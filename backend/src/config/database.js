const path = require('path');
const fs = require('fs');
const { Sequelize } = require('sequelize');
require('dotenv').config();

const storagePath = process.env.DB_STORAGE || './data/archisurance.sqlite';
const resolvedPath = path.isAbsolute(storagePath)
  ? storagePath
  : path.join(__dirname, '..', '..', storagePath);

// Ensure the data directory exists (SQLite needs the folder to already exist)
const dataDir = path.dirname(resolvedPath);
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: resolvedPath,
  logging: false,
});

module.exports = sequelize;
