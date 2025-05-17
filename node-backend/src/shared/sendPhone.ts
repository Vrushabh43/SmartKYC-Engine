import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';

const isDevelopment = process.env.NODE_ENV === 'development';

const snsClient = !isDevelopment
  ? new SNSClient({
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
      },
      region: process.env.AWS_REGION || 'us-east-1',
    })
  : null;

export const sendPhone = async (to: string, message: string) => {
  if (isDevelopment) {
    console.log('Development Mode - SMS would be sent to:', to);
    console.log('Message:', message);
    return Promise.resolve({ MessageId: 'dev-message-id' });
  }

  const params = {
    Message: message,
    PhoneNumber: to,
  };

  try {
    const command = new PublishCommand(params);
    const response = await snsClient.send(command);
    return response;
  } catch (error) {
    console.error('Error sending SMS:', error);
    throw error;
  }
};
