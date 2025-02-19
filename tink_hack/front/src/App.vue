<template>
  <div id="app">
    <img src="/logo.jpg" alt="Logo" class="logo">
    <div class="chat-container">
      <div class="messages" ref="messagesContainer">
        <div v-for="(message, index) in messages" :key="index" class="message-wrapper">
          <div v-if="['bot', 'father', 'daughter'].includes(message.type)" class="message-with-author">
            <img :src="`/${message.type}-icon.png`" 
                 :alt="message.type" 
                 class="message-icon left-icon">
            <div :class="['message', message.type, { 'with-audio': message.audioSrc }]">
              <div class="author-name" :class="message.type">{{ getAuthorName(message.type) }}</div>
              <div class="message-content">{{ message.text }}</div>
              <AudioPlayer v-if="message.audioSrc" :audioSrc="message.audioSrc" :isBotMessage="true" />
            </div>
          </div>
          <div v-else-if="message.type === 'audio'" class="message-with-author">
            <img src="/bot-icon.png" alt="bot" class="message-icon left-icon">
            <div class="message bot with-audio">
              <AudioPlayer :audioSrc="message.audioSrc" :isBotMessage="true" />
            </div>
          </div>
          <div v-else :class="['message', message.type]">
            <div class="message-content">{{ message.text }}</div>
          </div>
        </div>
        <div v-if="isTyping" class="message-wrapper">
          <div class="typing">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
      <div class="input-container">
        <button @click="triggerFileUpload" class="attach-file-btn" :disabled="isTyping">
          <img src="/paperclip.png" alt="Прикрепить файл" class="attach-icon">
        </button>
        <div class="input-wrapper">
          <textarea 
            v-model="currentMessage" 
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.shift.enter="handleShiftEnter"
            @input="autoResize"
            placeholder="Введите ваше сообщение..." 
            ref="messageInput"
            :disabled="isTyping"
          ></textarea>
        </div>
        <button @click="sendMessage" class="send-button" :disabled="!currentMessage.trim() || isTyping">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="send-icon">
            <path d="M12 3.586L5.707 9.879a1 1 0 1 0 1.414 1.414L11 7.414V19a1 1 0 1 0 2 0V7.414l3.879 3.879a1 1 0 0 0 1.414-1.414L12 3.586z"/>
          </svg>
        </button>
      </div>
    </div>
    <input
      type="file"
      ref="fileInput"
      style="display: none"
      @change="handleFileUpload"
    />
  </div>
</template>

<script>
import axios from 'axios';
import AudioPlayer from './AudioPlayer.vue';

export default {
  components: {
    AudioPlayer
  },
  data() {
    return {
      currentMessage: '',
      messages: [
        { type: 'bot', text: 'Здравствуйте! Чем я могу вам помочь?' }
      ],
      selectedFile: null,
      isTyping: false,
    };
  },
  methods: {
    async sendMessage() {
      if (!this.currentMessage.trim() || this.isTyping) return;

      this.messages.push({ type: 'user', text: this.currentMessage });
      const userMessage = this.currentMessage;
      this.currentMessage = '';

      this.isTyping = true;
      this.$nextTick(() => {
        this.scrollToBottom();
      });

      try {
        const response = await axios.post('http://localhost:8000/chat', null, {
          params: { message: userMessage }
        });
        
        this.isTyping = false;
        // Добавляем задержку перед выводом каждого сообщения
        for (const msg of response.data.responses) {
          await this.addMessageWithDelay(msg);
        }
        
        // Добавляем аудиосообщение после текстовых сообщений
        if (response.data.audioSrc) {
          await this.addMessageWithDelay({
            type: 'audio',
            audioSrc: `http://localhost:8000${response.data.audioSrc}`
          });
        }
      } catch (error) {
        this.isTyping = false;
        console.error('Ошибка при отправке сообщения:', error);
        this.messages.push({ type: 'bot', text: 'Извините, произошла ошибка при обработке вашего сообщения.' });
      }

      this.$nextTick(() => {
        this.scrollToBottom();
      });
    },
    addMessageWithDelay(message) {
      return new Promise(resolve => {
        setTimeout(() => {
          this.messages.push(message);
          this.$nextTick(() => {
            this.scrollToBottom();
          });
          resolve();
        }, 500); // Задежка в 0.5 секунды
      });
    },
    scrollToBottom() {
      const container = this.$refs.messagesContainer;
      container.scrollTop = container.scrollHeight;
    },
    triggerFileUpload() {
      this.$refs.fileInput.click();
    },
    async handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        const formData = new FormData();
        formData.append('file', file);

        this.isTyping = true;
        this.$nextTick(() => {
          this.scrollToBottom();
        });

        try {
          const response = await axios.post('http://localhost:8000/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          });
          
          this.isTyping = false;
          
          // Добавляем задержку перед выводом каждого сообщения
          for (const msg of response.data.responses) {
            await this.addMessageWithDelay(msg);
          }

          // Добавляем аудиосообщение после текстовых сообщений
          if (response.data.audioSrc) {
            await this.addMessageWithDelay({
              type: 'audio',
              audioSrc: `http://localhost:8000${response.data.audioSrc}`
            });
          }
        } catch (error) {
          this.isTyping = false;
          console.error('Error uploading file:', error);
          await this.addMessageWithDelay({ type: 'bot', text: 'Извините, произошла ошибка при загрузке файла.' });
        }

        this.$nextTick(() => {
          this.scrollToBottom();
        });
      }
    },
    getAuthorName(type) {
      const names = {
        bot: 'Бот',
        father: 'Отец',
        daughter: 'Дочь'
      };
      return names[type] || type;
    },
    handleShiftEnter(event) {
      event.preventDefault();
      const textarea = event.target;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const value = textarea.value;
      textarea.value = value.substring(0, start) + '\n' + value.substring(end);
      textarea.selectionStart = textarea.selectionEnd = start + 1;
      this.autoResize();
    },
    autoResize() {
      const textarea = this.$refs.messageInput;
      textarea.style.height = 'auto';
      const singleLineHeight = 20; // Прмерная высота одо строки
      const newHeight = Math.max(textarea.scrollHeight, singleLineHeight);
      textarea.style.height = `${Math.min(newHeight, 100)}px`; // Ограничиваем максимальную высоту
      textarea.style.overflowY = newHeight > 100 ? 'auto' : 'hidden';
    }
  },
  mounted() {
    this.autoResize(); // Вызываем при монтировании компонента
  },
  updated() {
    this.autoResize(); // Вызываем при обновлении компонента
  }
};
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400&display=swap');

:root {
  --background-color: #F0F2F5;
  --chat-background: #FFFFFF;
  --text-color: #333333;
  --input-background: #F0F0F0;
  --bot-message-bg: #E8E8E8;
  --father-message-bg: #E8E8E8;
  --daughter-message-bg: #E8E8E8; /* Теперь такой же, как у бота */
  --user-message-bg: #428bf9;
  --user-message-color: #FFFFFF;
  --accent-color: #428bf9;
  --main-font: 'Roboto', sans-serif;
}

body {
  margin: 0;
  padding: 0;
  font-family: var(--main-font);
  font-weight: 400;
  background-color: var(--chat-background);
  color: var(--text-color);
  font-size: 18px; /* Увеличено с 16px */
}

#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--chat-background);
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100% - 8%); /* Уменьшаем высоту на 60px для отступа сверху */
  max-width: 800px;
  margin: 60px auto 0; /* Добавляем оступ свеху */
  width: 100%;
  background-color: var(--chat-background);
  border-radius: 10px; /* Добавляем скругление уов */
}

.messages {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}

/* Стили для WebKit браузеров (Chrome, Safari, новые версии Edge) */
.messages::-webkit-scrollbar {
  width: 8px;
}

.messages::-webkit-scrollbar-track {
  background: transparent;
}

.messages::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.2);
}

.message-wrapper {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px; /* Уменьшено с 20px */
  width: 100%;
}

.message {
  max-width: calc(80% - 56px);
  padding: 12px 16px;
  border-radius: 18px;
  margin-bottom: 4px;
  word-wrap: break-word;
  position: relative;
}

.message-icon {
  width: 40px;  /* Уменьшено с 44px */
  height: 40px; /* Уменьшено с 44px */
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 2px; /* Уменьшено с 4px */
}

.left-icon {
  margin-right: 10px; /* Уменьшено с 12px */
}

.message-content {
  line-height: 1.4; /* Увеличено с 1.3 */
  margin-top: 0;
  font-size: 18px; /* Увеличено с 16px */
  font-family: var(--main-font);
  font-weight: 400;
  white-space: pre-wrap;
}

.message.with-audio {
  width: 300px;
  max-width: 80%;
  padding-top: 12px; /* Уменьшаем верхний отступ для сообщений с аудио */
}

.message.bot, .message.father, .message.daughter {
  background-color: #E8E8E8;
  align-self: flex-start;
  border-bottom-left-radius: 6px; /* Менее острый угол слева внизу */
  padding-top: 22px; /* Оставляем место для имени автора */
}

.message.user {
  background-color: #428bf9;
  color: #FFFFFF;
  align-self: flex-end;
  margin-left: auto;
  border-bottom-right-radius: 6px; /* Менее острый угол справа внизу */
  padding-top: 12px; /* Уменьшаем верхний отступ для сообщений пользователя */
}

.message-content {
  margin-bottom: 5px;
}

.message.bot .audio-player,
.message.father .audio-player,
.message.daughter .audio-player {
  margin-top: 5px;
}

.input-container {
  display: flex;
  align-items: center;
  padding: 10px 20px; /* Уменьшаем вертикальный отступ */
  background-color: var(--chat-background);
  border-top: 1px solid var(--input-background);
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
}

.attach-file-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-right: 10px;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
}

.attach-icon {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.input-wrapper {
  position: relative;
  flex-grow: 1;
  margin-right: 10px;
  display: flex;
  align-items: center; /* Возвращаем center для вертикального выравнивания */
}

textarea {
  width: 100%;
  padding: 10px 16px; /* Немного увеличены отступы */
  border: 1px solid var(--input-background);
  border-radius: 12px;
  font-size: 18px; /* Увеличено с 16px */
  font-family: var(--main-font);
  font-weight: 400;
  outline: none;
  background-color: var(--input-background);
  color: var(--text-color);
  resize: none;
  min-height: 40px; /* Немного увеличено */
  max-height: 120px; /* Увеличено с 100px */
  box-sizing: border-box;
  transition: height 0.1s ease;
  line-height: 24px;
  overflow-y: hidden;
}

.send-button {
  background-color: var(--accent-color);
  border: none;
  cursor: pointer;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: opacity 0.3s ease;
  padding: 0;
  flex-shrink: 0;
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-icon {
  width: 28px;
  height: 28px;
  fill: white; /* Делаем стрелочку отпрвки сообщения белой */
}

@media (max-width: 768px) {
  .message {
    max-width: 85%;
  }
}

.logo {
  position: fixed;
  top: 25px;
  left: 30px;
  width: 200px;
  height: auto;
  z-index: 1000;
}

.message-with-author {
  display: flex;
  align-items: flex-start;
  width: 100%;
  margin-bottom: 12px; /* Уменьшено с 16px */
}

.author-name {
  font-size: 13px; /* Увеличено с 11px */
  font-weight: 700;
  position: absolute;
  top: 5px; /* Немного увеличено */
  left: 16px;
  color: #888;
}

.author-name.father {
  color: #4a69bd;
}

.author-name.daughter {
  color: #e84393;
}

.message-icon {
  width: 40px;  /* Уменьшено с 44px */
  height: 40px; /* Уменьшено с 44px */
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 2px; /* Уменьшено с 4px */
}

.left-icon {
  margin-right: 10px; /* Уменьше��о с 12px */
}

.message-content {
  line-height: 1.3;
  margin-top: 0;
  font-size: 16px;
}

.message.user .author-name {
  display: none; /* Скрываем имя автора для сообщений пользователя */
}

/* ... остальные стили остаются без изменений ... */

textarea {
  width: 100%;
  padding: 8px 14px;
  border: 1px solid var(--input-background);
  border-radius: 12px;
  font-size: 16px;
  font-family: var(--main-font);
  font-weight: 400;
  outline: none;
  background-color: var(--input-background);
  color: var(--text-color);
  resize: none;
  min-height: 36px;
  max-height: 100px;
  box-sizing: border-box;
  transition: height 0.1s ease;
  line-height: 20px;
  overflow-y: hidden;
}

.message-content {
  line-height: 1.3;
  margin-top: 0;
  font-size: 16px;
  font-family: var(--main-font);
  font-weight: 400;
  white-space: pre-wrap;
}

/* ... остальные стили ... */

.typing {
  padding: 8px 12px;
  background-color: var(--bot-message-bg);
  border-radius: 18px;
  border-bottom-left-radius: 6px; /* Менее острый нижний левый угол */
  max-width: calc(85% - 48px);
  position: relative;
  min-height: 30px;
  margin-bottom: 0;
  margin-left: 44px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.typing-indicator {
  display: flex;
  align-items: center;
  padding-left: 4px; /* Добавляем небольой отступ слева */
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: #606060;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
  animation: typing 1s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.4s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.6s;
  margin-right: 0;
}

@keyframes typing {
  0% {
    transform: translateY(0px);
  }
  28% {
    transform: translateY(-5px);
  }
  44% {
    transform: translateY(0px);
  }
}

/* ... остальные стили ... */

.attach-file-btn:disabled,
.send-button:disabled,
textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ... остальные стили ... */

.message.bot .audio-player {
  margin-top: 5px;
  width: 100%; /* Добавлено для расширения плеера на всю ширину сообщения */
}

.message.user + .message-with-author {
  margin-top: 16px; /* Уменьшено с 20px */
}

.message-icon {
  width: 40px;  /* Уменьшено с 44px */
  height: 40px; /* Уменьшено с 44px */
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 2px; /* Уменьшено с 4px */
}

.left-icon {
  margin-right: 10px; /* Уменьшено с 12px */
}

.message-with-author {
  display: flex;
  align-items: flex-start;
  width: 100%;
  margin-bottom: 12px; /* Уменьшено с 16px */
}

.message {
  max-width: calc(80% - 56px); /* Уменьшено максимальную ширину сообщения, чтобы учесть увеличенную иконку */
  /* ... остальные стили ... */
}

/* ... остальные стили ... */
</style>





