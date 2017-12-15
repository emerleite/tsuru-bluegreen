package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
)

type Response struct {
	Cname []string `json:"cname"`
}

func GetCname(app string) string {
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
	if len(r.Cname) > 0 {
		return r.Cname[0]
	}
	return ""
}

func main() {
	cnameCommand := flag.NewFlagSet("cname", flag.ExitOnError)

//	fmt.Println(flag.Args())

	// Verify that a subcommand has been provided
	// os.Arg[0] is the main command
	// os.Arg[1] will be the subcommand
	if len(os.Args) < 2 {
		fmt.Println("list or count subcommand is required")
		os.Exit(1)
	}

	switch os.Args[1] {
	case "cname":
		cnameCommand.Parse(os.Args[2:])

	default:
		flag.PrintDefaults()
		os.Exit(1)
	}

	if cnameCommand.Parsed() {
		fmt.Println(GetCname("login-green"))
	}
}
