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
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Seed dummy data on startup if empty
async function seedInitialData() {
  const count = await prisma.student.count();
  if (count === 0) {
    const cam = await prisma.camera.create({
      data: { camCode: 'CAM-01', location: 'Main Gate North' }
    });

    const students = [
      { rollNumber: '1001', name: 'Aarav Sharma', gradeClass: 'Class 10-A', parentPhone: '+919876543210' },
      { rollNumber: '1002', name: 'Priya Verma', gradeClass: 'Class 12-B', parentPhone: '+919876543211' },
      { rollNumber: '1003', name: 'Rohan Gupta', gradeClass: 'Class 9-C', parentPhone: '+919876543212' },
      { rollNumber: '1004', name: 'Ananya Singh', gradeClass: 'Class 11-A', parentPhone: '+919876543213' }
    ];

    for (const s of students) {
      const student = await prisma.student.create({ data: s });
      await prisma.attendanceLog.create({
        data: {
          studentId: student.id,
          cameraId: cam.id,
          confidenceScore: 99.4,
          status: 'PRESENT'
        }
      });
    }
    console.log('✅ Initial Seed Complete!');
  }
}
seedInitialData();

// ================= API ROUTES =================

// 1. Dashboard Stats
app.get('/api/stats', async (req, res) => {
  try {
    const total = await prisma.student.count();
    const present = await prisma.attendanceLog.count({ where: { status: 'PRESENT' } });
    const late = await prisma.attendanceLog.count({ where: { status: 'LATE' } });
    const absent = Math.max(0, total - (present + late));

    res.json({ total, present, late, absent });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 2. Attendance Logs Table
app.get('/api/attendance', async (req, res) => {
  try {
    const logs = await prisma.attendanceLog.findMany({
      include: { student: true, camera: true },
      orderBy: { timestamp: 'desc' },
      take: 20
    });
    res.json(logs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3. Trigger CCTV Face Recognition Event
app.post('/api/scan', async (req, res) => {
  try {
    const students = await prisma.student.findMany();
    const cameras = await prisma.camera.findMany();
    
    if (students.length === 0 || cameras.length === 0) {
      return res.status(400).json({ error: 'No students or cameras in DB' });
    }

    const randomStudent = students[Math.floor(Math.random() * students.length)];
    const randomCam = cameras[0];
    const isLate = Math.random() > 0.7;
    const confidence = (98 + Math.random() * 1.9).toFixed(1);

    const log = await prisma.attendanceLog.create({
      data: {
        studentId: randomStudent.id,
        cameraId: randomCam.id,
        confidenceScore: parseFloat(confidence),
        status: isLate ? 'LATE' : 'PRESENT'
      },
      include: { student: true, camera: true }
    });

    // Real-time Push Event via WebSockets
    const eventPayload = {
      id: log.id,
      name: log.student.name,
      roll: log.student.rollNumber,
      gradeClass: log.student.gradeClass,
      location: log.camera.location,
      confidence: log.confidenceScore,
      status: log.status,
      time: new Date(log.timestamp).toLocaleTimeString()
    };

    io.emit('newDetection', eventPayload);
    res.status(201).json({ success: true, log: eventPayload });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Serve Single Page App
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 5000;
server.listen(PORT, () => console.log(`🚀 EduVision AI running on http://localhost:${PORT}`));

// New Commit
// New Student Registration Route
app.post('/api/students/register', async (req, res) => {
  try {
    const { name, rollNumber, gradeClass, parentPhone, faceData } = req.body;
    
    const student = await prisma.student.create({
      data: {
        name,
        rollNumber,
        gradeClass,
        parentPhone
      }
    });

    res.status(201).json({ success: true, student });
  } catch (err) {
    res.status(400).json({ error: 'Roll Number already exists or invalid data!' });
  }
});
