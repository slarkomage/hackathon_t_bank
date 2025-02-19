<template>
  <div class="audio-player" :class="{ 'bot': isBotMessage }">
    <audio ref="audioPlayer" :src="audioSrc" @loadedmetadata="onLoadedMetadata" @timeupdate="onTimeUpdate" @ended="onEnded"></audio>
    <button @click="togglePlay" class="play-pause-btn">
      <svg v-if="!isPlaying" viewBox="0 0 24 24" class="play-icon">
        <circle cx="12" cy="12" r="11" fill="#3390ec"/>
        <path d="M9.5 7v10l8-5-8-5z" fill="#ffffff"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" class="pause-icon">
        <circle cx="12" cy="12" r="11" fill="#3390ec"/>
        <rect x="8" y="7" width="3" height="10" fill="#ffffff"/>
        <rect x="13" y="7" width="3" height="10" fill="#ffffff"/>
      </svg>
    </button>
    <div class="audio-content">
      <div class="progress-container" @click="seekAudio">
        <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
      </div>
      <div class="audio-info">
        <span class="time-display">{{ formatTime(currentTime) }}</span>
        <span class="audio-name">Голосовое сообщение</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    audioSrc: {
      type: String,
      required: true
    },
    isBotMessage: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isPlaying: false,
      duration: 0,
      currentTime: 0
    }
  },
  computed: {
    progress() {
      return (this.currentTime / this.duration) * 100 || 0;
    }
  },
  methods: {
    togglePlay() {
      if (this.isPlaying) {
        this.$refs.audioPlayer.pause();
      } else {
        this.$refs.audioPlayer.play();
      }
      this.isPlaying = !this.isPlaying;
    },
    onLoadedMetadata() {
      this.duration = this.$refs.audioPlayer.duration;
    },
    onTimeUpdate() {
      this.currentTime = this.$refs.audioPlayer.currentTime;
    },
    onEnded() {
      this.isPlaying = false;
      this.currentTime = 0;
    },
    seekAudio(event) {
      const progressBar = event.currentTarget;
      const clickPosition = event.clientX - progressBar.getBoundingClientRect().left;
      const percentClicked = clickPosition / progressBar.offsetWidth;
      this.$refs.audioPlayer.currentTime = percentClicked * this.duration;
    },
    formatTime(time) {
      const minutes = Math.floor(time / 60);
      const seconds = Math.floor(time % 60);
      return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }
  },
  watch: {
    audioSrc: {
      immediate: true,
      handler(newSrc) {
        if (newSrc) {
          this.$nextTick(() => {
            this.$refs.audioPlayer.load();
          });
        }
      }
    }
  }
}
</script>

<style scoped>
.audio-player {
  display: flex;
  align-items: center;
  background-color: transparent;
  width: 100%;
  padding: 8px 0;
}

.play-pause-btn {
  background: none;
  border: none;
  width: 44px;
  height: 44px;
  cursor: pointer;
  margin-right: 10px;
  padding: 0;
  flex-shrink: 0;
}

.play-icon, .pause-icon {
  width: 44px;
  height: 44px;
}

.audio-player.bot .play-pause-btn svg circle {
  fill: #3390ec;
}

.audio-player.bot .play-pause-btn svg path,
.audio-player.bot .play-pause-btn svg rect {
  fill: #ffffff;
}

.audio-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.progress-container {
  height: 3px;
  background-color: rgba(51, 144, 236, 0.2);
  position: relative;
  cursor: pointer;
  margin-bottom: 5px;
  border-radius: 1.5px;
}

.progress-bar {
  height: 100%;
  background-color: #3390ec;
  position: absolute;
  top: 0;
  left: 0;
  transition: width 0.1s linear;
  border-radius: 1.5px;
}

.audio-player.bot .progress-container {
  background-color: rgba(0, 0, 0, 0.1);
}

.audio-player.bot .progress-bar {
  background-color: #707579;
}

.audio-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.time-display {
  color: #3390ec;
  font-weight: bold;
}

.audio-player.bot .time-display {
  color: #707579;
}

.audio-name {
  color: #707579;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
