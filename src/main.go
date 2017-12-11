package main

import (
	"os"
	"fmt"
	"net/http"
	"encoding/json"
)

type Response struct {
	Cname []string `json:"cname"`
}

func get_cname(app string) string {
	token := os.Getenv("TSURU_TOKEN")
	target := os.Getenv("TSURU_TARGET")
	url := fmt.Sprintf("%s/apps/%s", target, app)

	client := &http.Client{}
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("Authorization", fmt.Sprintf("bearer %s", token))
	resp, err := client.Do(req)
	if err != nil {
		return ""
	}
	defer resp.Body.Close()
	r := new(Response)
	json.NewDecoder(resp.Body).Decode(r)
	return r.Cname[0]
}

func main() {
	fmt.Println(get_cname("login-green"))
}
