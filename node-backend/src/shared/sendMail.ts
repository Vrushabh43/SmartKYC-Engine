import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';

const isDevelopment = process.env.NODE_ENV === 'development';

const sesClient = !isDevelopment
  ? new SESClient({
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
      },
      region: process.env.AWS_REGION || 'us-east-1',
    })
  : null;

export const sendMail = async (to: string, subject: string, body: string) => {
  if (isDevelopment) {
    console.log('Development Mode - Email would be sent to:', to);
    console.log('Subject:', subject);
    console.log('Body:', body);
    return Promise.resolve({ MessageId: 'dev-email-id' });
  }

  const params = {
    Source: process.env.EMAIL_FROM,
    Destination: {
      ToAddresses: [to],
    },
    Message: {
      Subject: {
        Data: subject,
      },
      Body: {
        Text: {
          Data: body,
        },
      },
    },
  };

  try {
    const command = new SendEmailCommand(params);
    const response = await sesClient.send(command);
    return response;
  } catch (error) {
    console.error('Error sending email:', error);
    throw error;
  }
};
