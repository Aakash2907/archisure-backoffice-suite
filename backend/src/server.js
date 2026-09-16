require('dotenv').config();
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const { notFound, errorHandler } = require('./middleware/errorHandler');

// Ensure DB + schema are initialized before routes are loaded
require('./db');

const app = express();

app.use(cors({ origin: process.env.CORS_ORIGIN || '*' }));
app.use(express.json());
app.use(morgan('dev'));

app.get('/api/health', (req, res) => res.json({ status: 'ok', service: 'archisurance-backend' }));

app.use('/api/auth', require('./routes/auth'));
app.use('/api/customers', require('./routes/customers'));
app.use('/api/interactions', require('./routes/interactions'));
app.use('/api/devices', require('./routes/devices'));
app.use('/api/behaviors', require('./routes/behaviors'));
app.use('/api/products', require('./routes/products'));
app.use('/api/policies', require('./routes/policies'));
app.use('/api/payments', require('./routes/payments'));
app.use('/api/revenue', require('./routes/revenue'));
app.use('/api/costs', require('./routes/costs'));
app.use('/api/financial', require('./routes/financial'));
app.use('/api/analytics', require('./routes/analytics'));
app.use('/api/dashboard', require('./routes/dashboard'));
app.use('/api/notifications', require('./routes/notifications'));

app.use(notFound);
app.use(errorHandler);
