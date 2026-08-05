const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const path = require('path');
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();
const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// Calculate distance between two face vectors
function euclideanDistance(arr1, arr2) {
  return Math.sqrt(arr1.reduce((sum, val, i) => sum + Math.pow(val - arr2[i], 2), 0));
}

// Default Camera Setup
async function initCam() {
  const cam = await prisma.camera.findFirst();
  if (!cam) {
    await prisma.camera.create({ data: { camCode: 'CAM-01', location: 'Main Gate North' } });
  }
}
initCam();

// 1. Student Registration with Face Vector
app.post('/api/students/register', async (req, res) => {
  try {
    const { name, rollNumber, gradeClass, parentPhone, faceDescriptor } = req.body;
    
    const student = await prisma.student.create({
      data: {
        name,
        rollNumber,
        gradeClass,
        parentPhone,
        faceDescriptor: faceDescriptor ? JSON.stringify(faceDescriptor) : null
      }
    });

    res.status(201).json({ success: true, student });
  } catch (err) {
    res.status(400).json({ error: 'Roll Number already exists!' });
  }
});

// 2. Real AI Face Matching Route
app.post('/api/recognize', async (req, res) => {
  try {
    const { faceDescriptor } = req.body;
    if (!faceDescriptor) return res.status(400).json({ error: 'No face descriptor provided' });

    const students = await prisma.student.findMany({
      where: { faceDescriptor: { not: null } }
    });

    if (students.length === 0) {
      return res.status(404).json({ error: 'Pehle student ko register karein!' });
    }

    let bestMatch = null;
    let lowestDistance = Infinity;

    for (const student of students) {
      const savedVector = JSON.parse(student.faceDescriptor);
      const distance = euclideanDistance(faceDescriptor, savedVector);
      if (distance < lowestDistance) {
        lowestDistance = distance;
        bestMatch = student;
      }
    }

    // Matching Distance Threshold < 0.6
    if (bestMatch && lowestDistance < 0.6) {
      const camera = await prisma.camera.findFirst();
      const isLate = new Date().getHours() >= 10;
      const accuracy = Math.max(88, Math.min(99.9, ((1 - lowestDistance) * 100))).toFixed(1);

      const log = await prisma.attendanceLog.create({
        data: {
          studentId: bestMatch.id,
          cameraId: camera ? camera.id : 'default-cam',
          confidenceScore: parseFloat(accuracy),
          status: isLate ? 'LATE' : 'PRESENT'
        },
        include: { student: true, camera: true }
      });

      const eventPayload = {
        name: log.student.name,
        roll: log.student.rollNumber,
        gradeClass: log.student.gradeClass,
        location: log.camera ? log.camera.location : 'Main Gate',
        confidence: log.confidenceScore,
        status: log.status,
        time: new Date(log.timestamp).toLocaleTimeString()
      };

      io.emit('newDetection', eventPayload);
      return res.json({ success: true, match: eventPayload });
    } else {
      return res.status(404).json({ error: 'Face not matched! Please register first.' });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Stats APIs
app.get('/api/stats', async (req, res) => {
  const total = await prisma.student.count();
  const present = await prisma.attendanceLog.count({ where: { status: 'PRESENT' } });
  const late = await prisma.attendanceLog.count({ where: { status: 'LATE' } });
  const absent = Math.max(0, total - (present + late));
  res.json({ total, present, late, absent });
});

app.get('/api/attendance', async (req, res) => {
  const logs = await prisma.attendanceLog.findMany({
    include: { student: true, camera: true },
    orderBy: { timestamp: 'desc' },
    take: 20
  });
  res.json(logs);
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => console.log(`🚀 Server running on port ${PORT}`));
