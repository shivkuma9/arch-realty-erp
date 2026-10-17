const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

// Read .env.local or .env
function loadEnv() {
  const envPath = fs.existsSync('.env.local') ? '.env.local' : '.env';
  if (!fs.existsSync(envPath)) {
    console.error(`Env file ${envPath} not found`);
    process.exit(1);
  }
  const content = fs.readFileSync(envPath, 'utf8');
  content.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx !== -1) {
      const key = trimmed.slice(0, eqIdx).trim();
      let val = trimmed.slice(eqIdx + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      process.env[key] = val;
    }
  });
}

loadEnv();

async function testNeon() {
  const connectionString = process.env.DATABASE_URL;
  console.log('Connecting to Neon PostgreSQL service...');
  console.log(`Endpoint host: ${new URL(connectionString).host}`);
  console.log(`Branch: ${process.env.NEON_BRANCH || 'production'}`);

  const client = new Client({
    connectionString,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log('[SUCCESS] Connected to Neon PostgreSQL database!');

    const res = await client.query('SELECT current_database() as db, current_user as user, version() as version, NOW() as current_timestamp;');
    console.log('[OK] Database Info:');
    console.log(`     - Database: ${res.rows[0].db}`);
    console.log(`     - User: ${res.rows[0].user}`);
    console.log(`     - Server Time: ${res.rows[0].current_timestamp}`);
    console.log(`     - Engine: ${res.rows[0].version.split(',')[0]}`);

    // End to end test table
    console.log('\nTesting End-to-End Table Write & Read Operations:');
    await client.query('CREATE TABLE IF NOT EXISTS _neon_healthcheck (id serial primary key, service text, checked_at timestamptz default now());');
    await client.query("INSERT INTO _neon_healthcheck (service) VALUES ('arch-realty-erp-crm');");
    const countRes = await client.query('SELECT count(*) as total FROM _neon_healthcheck;');
    console.log(`[SUCCESS] Table operations verified! Total health check rows in Neon: ${countRes.rows[0].total}`);

    // Clean up
    await client.query('DROP TABLE _neon_healthcheck;');
    console.log('[OK] Cleaned up temporary test table.');

    await client.end();
    console.log('\n>>> All Neon services wired and verified successfully end-to-end! <<<');
  } catch (err) {
    console.error('[ERROR] Neon connection failed:', err);
    process.exit(1);
  }
}

testNeon();
