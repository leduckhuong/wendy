import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

interface user {
    username: string,
    role: string,
    firstname: string,
    lastname: string,
    totpEnabled: boolean,
    roles: string
}

export default {
    user: {
        username: "",
        role: "",
        firstname: "",
        lastname: "",
        totpEnabled: false,
        roles: ""
    },

    getToken: function (
        username: string,
        password: string
      ): Promise<any> { // Hoặc thay `any` bằng kiểu cụ thể như `User`
        return new Promise((resolve, reject) => {
          const params = { username, password };
        axios
          .post(`/api/user/token`, params)
            .then((response) => {
              const token = response.data.datas.token;
              const user:user = jwtDecode(token);
              this.user = user;
              resolve(user);
            })
            .catch((error) => {
              reject(error);
            });
        });
    },

    register: function (
      username: string,
      password: string
    ): Promise<any> {
      return new Promise((resolve, reject) => {
        const params = { username, password };
        axios
          .post(`/api/user/init`, params)
          .then((response) => {
            resolve(response);
          })
          .catch((error) => {
            reject(error);
          });
      });
    }
      
};