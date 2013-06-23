# The structure of this plugin


## package build

this package contains the different build types and some tools to find them in a sublime project.

## package commands

commands contains all of the public commands that can invoked from sublime (mostly through shortcuts defined in the keymap file)

## package compiler

## package completion

Completion related logic, it is separated in multiple packages where each of them contains some logic for syntax specific completion (e.g. hx-files, hxml-files etc.)

## package panel

Interface for write messages to different panels.

## package project

Types and function for project management. It contains functions to access the current project and encapsulates the Project related state.

## package tools

The tools package contains helper functions for different data types. It also contains types and functions for general purpose.

## module codegen

## config

This module contains configuration and constants that can be accessed from other modules.

## module execute

## module haxelib

Haxelib related data structures and helper functions.

## module log

The module log contains functions for logging.

## module plugin

This module contains plugin related infos (path, sublime version etc.)

## module settings

This module contains some helper functions to access plugin or project settings. It encapsulates the logic to resolve settings in the right order.

## module temp

This module contains logic to create temporary classpaths and classes. That can be appended to builds.

## module types

