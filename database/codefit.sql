CREATE DATABASE IF NOT EXISTS codefit
    CHARACTER SET utf8mb4
    COLLATE utf8mb4unicode_ci;

USE codefit;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    edad INT NULL,
    peso DECIMAL(6,2) NULL,
    altura DECIMAL(4,2) NULL,
    objetivo VARCHAR(50) DEFAULT 'mejorar_condicion',
    nivel VARCHAR(30) DEFAULT 'principiante',
    dias_disponibles VARCHAR(255) DEFAULT '',
    minutos_disponibles INT DEFAULT 30,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ejercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    categoria VARCHAR(60) NOT NULL,
    dificultad VARCHAR(30) NOT NULL,
    descripcion TEXT NOT NULL,
    duracion VARCHAR(40) DEFAULT '',
    equipo VARCHAR(120) DEFAULT 'Sin equipo'
);

CREATE TABLE IF NOT EXISTS rutinas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    objetivo VARCHAR(50) NOT NULL,
    nivel VARCHAR(30) NOT NULL,
    duracion INT NOT NULL DEFAULT 30,
    descripcion TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rutina_ejercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rutina_id INT NOT NULL,
    ejercicio_id INT NOT NULL,
    series INT DEFAULT 3,
    repeticiones VARCHAR(40) DEFAULT '10-12',
    orden INT DEFAULT 1,
    FOREIGN KEY (rutina_id)
        REFERENCES rutinas (id)
        ON DELETE CASCADE,
    FOREIGN KEY (ejercicio_id)
        REFERENCES ejercicios (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS progreso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    fecha DATE NOT NULL,
    peso DECIMAL(6,2) NULL,
    minutos INT DEFAULT 0,
    entrenamiento VARCHAR(150) DEFAULT '',
    notas TEXT,
    FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id)
        ON DELETE CASCADE
);
