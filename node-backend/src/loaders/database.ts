import { Db, MongoClient } from 'mongodb';
import config from '../config';
import Logger from './logger';

let db: Db;
let client: MongoClient;

async function initializeClient(): Promise<Db> {
  try {
    client = await MongoClient.connect(config.databaseURL, {
      useUnifiedTopology: true,
      serverSelectionTimeoutMS: 5000, // 5 second timeout
    });

    Logger.info('Connected to MongoDB successfully');
    return client.db();
  } catch (error) {
    Logger.error('Failed to connect to MongoDB:', error);
    throw error;
  }
}

export default async (): Promise<Db> => {
  try {
    if (!db) {
      db = await initializeClient();
    }
    return db;
  } catch (error) {
    Logger.error('Database connection error:', error);
    throw error;
  }
};

// Handle process termination
process.on('SIGINT', async () => {
  if (client) {
    await client.close();
    Logger.info('MongoDB connection closed.');
  }
  process.exit(0);
});
